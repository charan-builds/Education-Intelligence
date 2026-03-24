from __future__ import annotations

import logging
import time

from fastapi import FastAPI, HTTPException, Request

from ai_service.config import get_ai_settings
from ai_service.schemas import (
    LearningPathRequest,
    LearningPathResponse,
    MentorResponse,
    MentorResponseRequest,
    ProgressAnalysisRequest,
    ProgressAnalysisResponse,
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    TopicExplainRequest,
    TopicExplainResponse,
)
from ai_service.service import AIOrchestrator

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Learning Platform AI Service", version="1.0.0")
settings = get_ai_settings()
orchestrator = AIOrchestrator(settings)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        logging.getLogger("ai_service").exception(
            "ai_request_failed",
            extra={"log_data": {"path": request.url.path, "latency_ms": latency_ms, "error_type": type(exc).__name__}},
        )
        raise
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    logging.getLogger("ai_service").info(
        "ai_request_completed",
        extra={"log_data": {"path": request.url.path, "status_code": response.status_code, "latency_ms": latency_ms}},
    )
    return response


@app.get("/health")
async def health() -> dict[str, str | bool]:
    return {"status": "ok", "llm_enabled": bool(settings.groq_api_key or settings.openai_api_key or settings.fallback_api_key)}


@app.post("/predict-learning-path", response_model=LearningPathResponse)
@app.post("/ai/generate-roadmap", response_model=LearningPathResponse)
async def generate_roadmap(payload: LearningPathRequest) -> LearningPathResponse:
    try:
        return await orchestrator.generate_roadmap(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI roadmap generation failed: {type(exc).__name__}") from exc


@app.post("/mentor-response", response_model=MentorResponse)
@app.post("/ai/mentor-chat", response_model=MentorResponse)
async def mentor_chat(payload: MentorResponseRequest) -> MentorResponse:
    try:
        return await orchestrator.mentor_chat(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI mentor response failed: {type(exc).__name__}") from exc


@app.post("/ai/analyze-progress", response_model=ProgressAnalysisResponse)
async def analyze_progress(payload: ProgressAnalysisRequest) -> ProgressAnalysisResponse:
    try:
        return await orchestrator.analyze_progress(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI progress analysis failed: {type(exc).__name__}") from exc


@app.post("/ai/explain-topic", response_model=TopicExplainResponse)
async def explain_topic(payload: TopicExplainRequest) -> TopicExplainResponse:
    try:
        return await orchestrator.explain_topic(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI topic explanation failed: {type(exc).__name__}") from exc


@app.post("/ai/generate-questions", response_model=QuestionGenerationResponse)
async def generate_questions(payload: QuestionGenerationRequest) -> QuestionGenerationResponse:
    try:
        return await orchestrator.generate_questions(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI question generation failed: {type(exc).__name__}") from exc
