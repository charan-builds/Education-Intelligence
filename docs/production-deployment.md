# Production Deployment

## Required services

- PostgreSQL 15+
- Redis 7+
- Celery worker and Celery beat
- Private S3-compatible bucket
- SendGrid account for transactional email

## Backend environment

Set these environment variables for the API and worker processes:

```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
CELERY_BROKER_URL=redis://...
CELERY_RESULT_BACKEND=redis://...
SECRET_KEY=change-me
APP_BASE_URL=https://app.example.com

S3_BUCKET_NAME=learning-platform-private
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_ENDPOINT_URL=
S3_PRESIGN_EXPIRY_SECONDS=900
UPLOAD_MAX_BYTES=25000000

EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid
EMAIL_SENDGRID_API_KEY=...
EMAIL_FROM_ADDRESS=no-reply@example.com
EMAIL_FROM_NAME=Learning Intelligence Platform
EMAIL_REPLY_TO=support@example.com
```

## Database rollout

Run migrations before deploying the API:

```bash
./.venv/bin/alembic upgrade head
```

The migration creates:

- `tenant_analytics_mv`
- `user_progress_summary_mv`

Those views are refreshed by the scheduled `jobs.refresh_precomputed_analytics` Celery beat task.

## Object storage

- Keep the bucket private.
- Do not expose public-read ACLs.
- Browser uploads should use `POST /files/upload-request`, then upload directly to the signed URL, then `POST /files/finalize`.
- Downloads should use `GET /files/{asset_id}` so the API can issue a short-lived signed URL.
- Enable S3 public access block for all four controls.
- Configure bucket CORS to allow `PUT` and `GET` from your frontend origins only.
- Grant the app IAM principal the minimum required permissions: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:HeadBucket`, `s3:GetBucketCors`, and `s3:GetPublicAccessBlock`.

## Email delivery

- Verification, reset, and invite emails are queued through `jobs.send_email`.
- Celery worker availability is required for async delivery and retries.
- For local development, set `EMAIL_ENABLED=false` or `EMAIL_PROVIDER=log`.
- For production SendGrid, verify the sender domain and configure SPF/DKIM before traffic cutover.

## Frontend deployment

Set:

```bash
NEXT_PUBLIC_API_URL=https://api.example.com
```

Deploy the frontend to Vercel or another static/container platform with server-side rendering support.

## Playwright runtime

If the host machine cannot install Chromium runtime libraries, run browser tests in the dedicated Playwright container:

```bash
docker build -f learning-platform-frontend/Dockerfile.e2e -t learning-platform-e2e .
docker run --rm --network host --env NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 learning-platform-e2e
```

On Ubuntu/Debian hosts, the equivalent native packages are:

```bash
apt-get update
apt-get install -y \
  libnspr4 \
  libnss3 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxrandr2 \
  libgbm1 \
  libasound2
npx playwright install --with-deps
```

## CI/CD

- `.github/workflows/ci.yml` runs backend tests plus frontend lint/build/test checks on pull requests.
- `.github/workflows/deploy.yml` handles container build and cluster deploy on `main`.

## Post-deploy checks

- `GET /health`
- `GET /metrics`
- register -> email verification request
- forgot password -> reset
- file upload request -> signed upload -> finalize
- analytics overview after the first MV refresh cycle

## Live integration validation

After production credentials are loaded into `.env` or your deployment secret store, run:

```bash
EMAIL_TEST_RECIPIENT=ops@example.com ./.venv/bin/python scripts/validate_external_integrations.py --email-to ops@example.com
```

That validator checks:

- S3 bucket reachability
- S3 public access block
- S3 CORS for `PUT` and `GET`
- presigned upload
- presigned download
- expired signed URL rejection
- cleanup of the temporary validation object
- live SendGrid API acceptance for a test email
