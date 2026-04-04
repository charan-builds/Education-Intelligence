# Delivery TODO

## Blueprint Alignment

- [x] Add first-class `independent_learner` role support across auth, routing, and panel redirects
- [x] Add `personal` tenant support for self-serve independent learner workspaces
- [x] Expose blueprint-friendly route aliases for auth, users, diagnostics, and roadmaps
- [x] Align learner-facing terminology toward `organization_name` while keeping compatibility
- [x] Make super-admin tenant views distinguish institution tenants from personal workspaces
- [x] Clean up demo seed data so seeded independent learners use `personal` tenants
- [x] Document seeded blueprint-aligned demo workspaces in [docs/demo_seed_data.md](/home/charan_derangula/projects/intelligentSystems/docs/demo_seed_data.md)

## Validation

- [x] Run Alembic upgrade through the new `personal` tenant migration
- [x] Reseed demo data and verify seeded personal workspaces plus institution tenants
- [x] Run focused backend blueprint and onboarding test suite
- [x] Run broader backend regression suite for auth, diagnostics, roadmaps, goals, and tenant isolation
- [x] Run frontend unit/build verification
- [x] Run live end-to-end learner journey checks against the running stack

## Stabilization

- [x] Fix any migration, seed, routing, auth, or panel regressions found during live checks
- [x] Tighten production readiness notes for email delivery, tenant setup, and roadmap generation
- [x] Confirm seeded credentials and panel URLs remain valid after rebuild/reseed
