from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ai_service.config import AISettings

logger = logging.getLogger("ai_service.llm")


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key: str
    model: str
    base_url: str | None
    timeout_seconds: float


class LLMClient:
    def __init__(self, settings: AISettings):
        self.settings = settings
        self.providers = self._build_providers(settings)
        self.enabled = bool(self.providers)
        self.clients = {
            provider.name: AsyncOpenAI(
                api_key=provider.api_key,
                base_url=provider.base_url,
                timeout=provider.timeout_seconds,
            )
            for provider in self.providers
        }

    @staticmethod
    def _build_providers(settings: AISettings) -> list[ProviderConfig]:
        providers: list[ProviderConfig] = []
        if settings.groq_api_key:
            providers.append(
                ProviderConfig(
                    name="groq",
                    api_key=settings.groq_api_key,
                    model=settings.groq_model,
                    base_url=settings.groq_base_url,
                    timeout_seconds=settings.groq_timeout_seconds,
                )
            )
        if settings.openai_api_key:
            providers.append(
                ProviderConfig(
                    name="openai_compatible",
                    api_key=settings.openai_api_key,
                    model=settings.openai_model,
                    base_url=settings.openai_base_url,
                    timeout_seconds=settings.openai_timeout_seconds,
                )
            )
        if settings.fallback_api_key:
            providers.append(
                ProviderConfig(
                    name="fallback",
                    api_key=settings.fallback_api_key,
                    model=settings.fallback_model,
                    base_url=settings.fallback_base_url,
                    timeout_seconds=settings.fallback_timeout_seconds,
                )
            )
        return providers

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _request_json(
        self,
        *,
        provider: ProviderConfig,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int,
    ) -> dict[str, Any]:
        client = self.clients[provider.name]
        started = time.perf_counter()
        response = await client.responses.create(
            model=provider.model,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ai_service_response",
                    "schema": {
                        "type": "object",
                        "additionalProperties": True,
                    },
                    "strict": False,
                }
            },
            temperature=self.settings.ai_temperature,
            max_output_tokens=max_output_tokens,
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        output_text = getattr(response, "output_text", "") or ""
        if not output_text:
            raise ValueError("Empty model response")
        data = json.loads(output_text)
        data["_provider"] = provider.name
        data["_model"] = provider.model
        data["_latency_ms"] = latency_ms
        logger.info(
            "llm_request_completed",
            extra={"log_data": {"provider": provider.name, "model": provider.model, "latency_ms": latency_ms}},
        )
        return data

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APITimeoutError)),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int = 900,
    ) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("No LLM provider is configured")

        failures: list[dict[str, str]] = []
        for provider in self.providers:
            try:
                return await self._request_json(
                    provider=provider,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_output_tokens=max_output_tokens,
                )
            except Exception as exc:
                logger.warning(
                    "llm_provider_failed",
                    extra={"log_data": {"provider": provider.name, "model": provider.model, "error": str(exc)}},
                )
                failures.append({"provider": provider.name, "error": str(exc)})

        raise RuntimeError(f"All LLM providers failed: {failures}")
