# Demo Seed Data

The demo seed pipeline is designed to make the platform feel active and believable instead of empty.
It also mirrors the current blueprint baseline so demos and QA runs exercise both institution tenants and self-serve independent learner workspaces.

## What it creates

- 5 realistic workspaces total:
  - 1 college tenant
  - 1 company tenant
  - 1 school tenant
  - 2 `personal` workspaces for independent learners
- 18 users total:
  - 1 platform super admin
  - 3 tenant admins
  - 3 tenant teachers
  - 3 tenant mentors
  - 9 tenant students
- 2 independent learners with their own personal tenants
- 9 goals
- 70 topics
- 280 questions
- completed diagnostics for each learner
- generated roadmaps with mixed completion states, revision steps, and foundation-gap coverage
- 30 days of learning activity per learner
- mentor suggestions, badges, communities, threads, replies, and upvotes
- experiment records to make dashboards feel more production-like

## Blueprint-aligned details

- Institution users belong to institution tenants and keep the familiar multi-panel setup.
- Independent learners are seeded into dedicated `personal` tenants instead of being grouped into a pseudo-institution tenant.
- Seeded profile payloads use the `organization_name` concept consistently, while remaining backward-compatible with the persisted `college_name` column.
- Each workspace includes topics, prerequisites, diagnostics, and roadmap steps so the end-to-end learner flow is easy to demo.

## Sample seeded access

- Platform:
  - `superadmin@platform.learnova.ai` / `SuperAdmin123!`
- Institution student example:
  - `maya.chen@demo.learnova.ai` / `Student123!`
- Independent learner examples:
  - `ava.martinez@workspace.learnova.ai` / `Student123!`
  - `leo.kim@workspace.learnova.ai` / `Student123!`

## How to run

```bash
cd backend
python seed.py
```

Docker bootstrap uses the same seed entrypoint through:

```bash
cd backend
python scripts/bootstrap_seed.py
```

## Sample API responses

After seeding, generate example payloads for demos or docs:

```bash
python scripts/generate_demo_api_samples.py
```

That writes JSON samples under `docs/demo_api_samples/`.
