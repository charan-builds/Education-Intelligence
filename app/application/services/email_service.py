from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.logging import bind_log_data, get_logger


@dataclass(slots=True)
class EmailPayload:
    to_email: str
    subject: str
    html_content: str
    text_content: str


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger()

    def _provider(self) -> str:
        return self.settings.email_provider.strip().lower()

    def _base_template(self, *, heading: str, intro: str, cta_label: str, cta_url: str, footer: str) -> tuple[str, str]:
        logo_block = ""
        if self.settings.email_template_logo_url:
            logo_block = (
                f'<img src="{self.settings.email_template_logo_url}" alt="Learning Intelligence Platform" '
                'style="height:40px;margin-bottom:24px;" />'
            )
        html_content = f"""
        <html>
          <body style="margin:0;background:#f8fafc;font-family:Arial,sans-serif;color:#0f172a;">
            <div style="max-width:640px;margin:0 auto;padding:32px 20px;">
              <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:24px;padding:32px;">
                {logo_block}
                <p style="margin:0 0 12px;font-size:12px;letter-spacing:0.24em;text-transform:uppercase;color:#64748b;">Learning Intelligence Platform</p>
                <h1 style="margin:0 0 16px;font-size:28px;line-height:1.2;">{heading}</h1>
                <p style="margin:0 0 24px;font-size:16px;line-height:1.7;color:#334155;">{intro}</p>
                <a href="{cta_url}" style="display:inline-block;background:#0f172a;color:#ffffff;text-decoration:none;padding:14px 22px;border-radius:999px;font-weight:700;">
                  {cta_label}
                </a>
                <p style="margin:24px 0 0;font-size:14px;line-height:1.7;color:#64748b;">{footer}</p>
              </div>
            </div>
          </body>
        </html>
        """.strip()
        text_content = f"{heading}\n\n{intro}\n\n{cta_label}: {cta_url}\n\n{footer}"
        return html_content, text_content

    def build_verification_email(self, *, to_email: str, verification_url: str) -> EmailPayload:
        html_content, text_content = self._base_template(
            heading="Verify your email",
            intro="Confirm your account to unlock diagnostics, roadmap generation, mentor guidance, and progress tracking.",
            cta_label="Verify email",
            cta_url=verification_url,
            footer="If you did not request this, you can safely ignore this message.",
        )
        return EmailPayload(
            to_email=to_email,
            subject="Verify your Learning Intelligence account",
            html_content=html_content,
            text_content=text_content,
        )

    def build_password_reset_email(self, *, to_email: str, reset_url: str) -> EmailPayload:
        html_content, text_content = self._base_template(
            heading="Reset your password",
            intro="Use the secure link below to choose a new password for your Learning Intelligence Platform account.",
            cta_label="Reset password",
            cta_url=reset_url,
            footer="If you did not request this reset, please review your account security.",
        )
        return EmailPayload(
            to_email=to_email,
            subject="Reset your Learning Intelligence password",
            html_content=html_content,
            text_content=text_content,
        )

    def build_invite_email(self, *, to_email: str, invite_url: str, role_label: str) -> EmailPayload:
        html_content, text_content = self._base_template(
            heading="You have been invited",
            intro=f"You have been invited to join the Learning Intelligence Platform as a {role_label.replace('_', ' ')}.",
            cta_label="Accept invite",
            cta_url=invite_url,
            footer="This invitation expires automatically for security reasons.",
        )
        return EmailPayload(
            to_email=to_email,
            subject="Your Learning Intelligence invitation",
            html_content=html_content,
            text_content=text_content,
        )

    async def send(self, payload: EmailPayload) -> dict[str, str | bool]:
        if not self.settings.email_enabled:
            self.logger.info(
                "email delivery skipped because email is disabled",
                extra=bind_log_data(event="email.skipped.disabled", to_email=payload.to_email, subject=payload.subject),
            )
            return {"status": "disabled", "provider": self._provider(), "delivered": False}

        provider = self._provider()
        if provider == "sendgrid":
            return await self._send_via_sendgrid(payload)
        if provider == "log":
            self.logger.info(
                "email payload logged",
                extra=bind_log_data(
                    event="email.logged",
                    to_email=payload.to_email,
                    subject=payload.subject,
                    preview=payload.text_content[:200],
                ),
            )
            return {"status": "logged", "provider": provider, "delivered": True}
        raise ValueError(f"Unsupported email provider: {provider}")

    async def _send_via_sendgrid(self, payload: EmailPayload) -> dict[str, str | bool]:
        api_key = self.settings.email_sendgrid_api_key
        if not api_key:
            raise ValueError("SendGrid API key is not configured")
        sender = {
            "email": self.settings.email_from_address,
            "name": self.settings.email_from_name,
        }
        message: dict[str, object] = {
            "personalizations": [{"to": [{"email": payload.to_email}]}],
            "from": sender,
            "subject": payload.subject,
            "content": [
                {"type": "text/plain", "value": payload.text_content},
                {"type": "text/html", "value": payload.html_content},
            ],
        }
        if self.settings.email_reply_to:
            message["reply_to"] = {"email": self.settings.email_reply_to}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=message,
            )
            response.raise_for_status()
        self.logger.info(
            "email delivered",
            extra=bind_log_data(event="email.delivered", provider="sendgrid", to_email=payload.to_email, subject=payload.subject),
        )
        return {"status": "queued", "provider": "sendgrid", "delivered": True}
