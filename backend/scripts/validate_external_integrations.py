#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.application.services.email_service import EmailPayload, EmailService
from app.core.config import get_settings

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:  # pragma: no cover
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore


@dataclass
class ValidationReport:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_pass(self, message: str) -> None:
        self.passed.append(message)

    def add_fail(self, message: str) -> None:
        self.failed.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.failed


def build_s3_client():
    settings = get_settings()
    if boto3 is None:
        raise RuntimeError("boto3 is not installed")
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
    )


def validate_s3(report: ValidationReport, *, prefix: str) -> None:
    settings = get_settings()
    missing = [
        name
        for name, value in {
            "S3_BUCKET_NAME": settings.s3_bucket_name,
            "S3_ACCESS_KEY_ID": settings.s3_access_key_id,
            "S3_SECRET_ACCESS_KEY": settings.s3_secret_access_key,
        }.items()
        if not value
    ]
    if missing:
        report.add_fail(f"S3 validation blocked: missing {', '.join(missing)}")
        return

    client = build_s3_client()
    bucket = str(settings.s3_bucket_name)
    object_key = f"{prefix.rstrip('/')}/{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex}.txt"
    body = b"learning-platform-s3-validation"

    try:
        client.head_bucket(Bucket=bucket)
        report.add_pass(f"S3 bucket reachable: {bucket}")
    except ClientError as exc:
        report.add_fail(f"S3 bucket access failed for {bucket}: {exc}")
        return

    try:
        public_block = client.get_public_access_block(Bucket=bucket)["PublicAccessBlockConfiguration"]
        required_flags = [
            "BlockPublicAcls",
            "IgnorePublicAcls",
            "BlockPublicPolicy",
            "RestrictPublicBuckets",
        ]
        if all(bool(public_block.get(flag)) for flag in required_flags):
            report.add_pass("S3 bucket public access block is fully enabled")
        else:
            report.add_fail(f"S3 bucket public access block is incomplete: {public_block}")
    except ClientError as exc:
        report.add_warning(f"Could not verify S3 public access block: {exc}")

    try:
        cors_rules = client.get_bucket_cors(Bucket=bucket)["CORSRules"]
        methods = {method for rule in cors_rules for method in rule.get("AllowedMethods", [])}
        if {"PUT", "GET"}.issubset(methods):
            report.add_pass("S3 bucket CORS includes GET and PUT")
        else:
            report.add_fail(f"S3 bucket CORS is missing required methods: {sorted(methods)}")
    except ClientError as exc:
        report.add_fail(f"S3 bucket CORS is missing or unreadable: {exc}")

    upload_url = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": bucket, "Key": object_key, "ContentType": "text/plain"},
        ExpiresIn=max(5, int(settings.s3_presign_expiry_seconds)),
    )

    with httpx.Client(timeout=30.0) as http:
        upload_response = http.put(upload_url, content=body, headers={"Content-Type": "text/plain"})
        if upload_response.status_code in {200, 201}:
            report.add_pass("S3 presigned upload succeeded")
        else:
            report.add_fail(f"S3 presigned upload failed with {upload_response.status_code}: {upload_response.text[:200]}")
            return

        download_url = client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": object_key, "ResponseContentType": "text/plain"},
            ExpiresIn=max(5, int(settings.s3_presign_expiry_seconds)),
        )
        download_response = http.get(download_url)
        if download_response.status_code == 200 and download_response.content == body:
            report.add_pass("S3 presigned download succeeded")
        else:
            report.add_fail(
                f"S3 presigned download failed with {download_response.status_code}: {download_response.text[:200]}"
            )

        expired_url = client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": object_key, "ResponseContentType": "text/plain"},
            ExpiresIn=1,
        )
        time.sleep(2)
        expired_response = http.get(expired_url)
        if expired_response.status_code >= 400:
            report.add_pass("Expired S3 signed URL is rejected")
        else:
            report.add_fail(f"Expired S3 signed URL unexpectedly succeeded with {expired_response.status_code}")

    try:
        client.delete_object(Bucket=bucket, Key=object_key)
        report.add_pass("S3 validation object cleanup succeeded")
    except ClientError as exc:
        report.add_warning(f"S3 validation object cleanup failed for {object_key}: {exc}")


async def validate_email(report: ValidationReport, *, recipient: str | None) -> None:
    settings = get_settings()
    if not settings.email_enabled:
        report.add_fail("Email validation blocked: EMAIL_ENABLED is false")
        return
    if settings.email_provider.strip().lower() != "sendgrid":
        report.add_fail(f"Email validation blocked: unsupported EMAIL_PROVIDER={settings.email_provider!r}")
        return
    if not settings.email_sendgrid_api_key:
        report.add_fail("Email validation blocked: EMAIL_SENDGRID_API_KEY is missing")
        return
    if not recipient:
        report.add_fail("Email validation blocked: --email-to recipient is required")
        return

    service = EmailService()
    sent_at = datetime.now(timezone.utc).isoformat()
    payload = EmailPayload(
        to_email=recipient,
        subject=f"Learning Platform integration validation {sent_at}",
        html_content=(
            "<html><body><h1>Integration validation</h1>"
            f"<p>This message confirms the production email provider is reachable.</p><p>Sent at {sent_at}</p>"
            "</body></html>"
        ),
        text_content=f"Integration validation\n\nThis message confirms the production email provider is reachable.\nSent at {sent_at}",
    )
    result = await service.send(payload)
    if result.get("delivered"):
        report.add_pass(f"Email provider accepted delivery to {recipient}")
    else:
        report.add_fail(f"Email provider did not accept delivery: {result}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate live S3 and email integrations for the Learning Intelligence Platform."
    )
    parser.add_argument("--skip-s3", action="store_true", help="Skip S3 validation")
    parser.add_argument("--skip-email", action="store_true", help="Skip email validation")
    parser.add_argument("--email-to", help="Recipient email address for live email validation")
    parser.add_argument(
        "--s3-prefix",
        default="integration-validation",
        help="Object key prefix used for temporary validation uploads",
    )
    return parser.parse_args()


def print_report(report: ValidationReport) -> None:
    for item in report.passed:
        print(f"PASS: {item}")
    for item in report.warnings:
        print(f"WARN: {item}")
    for item in report.failed:
        print(f"FAIL: {item}")


async def main() -> int:
    args = parse_args()
    report = ValidationReport()

    if not args.skip_s3:
      validate_s3(report, prefix=args.s3_prefix)
    if not args.skip_email:
      await validate_email(report, recipient=args.email_to)

    print_report(report)
    if report.ok:
        print("Integration validation completed successfully.")
        return 0
    print("Integration validation failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
