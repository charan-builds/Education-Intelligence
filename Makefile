.PHONY: smoke smoke-multitenant smoke-role-panels preflight verify-backend verify-frontend verify-e2e verify-integrations verify

smoke:
	./scripts/smoke_e2e.sh

smoke-multitenant:
	./scripts/smoke_multitenant.sh

smoke-role-panels:
	python scripts/smoke_role_panels.py

preflight:
	./scripts/preflight.sh

verify-backend:
	venv/bin/pytest -q

verify-frontend:
	cd learning-platform-frontend && npm run test:run && npm run build

verify-e2e:
	cd learning-platform-frontend && npm run test:e2e

verify-integrations:
	./.venv/bin/python scripts/validate_external_integrations.py --email-to $$EMAIL_TEST_RECIPIENT

verify: verify-backend verify-frontend
