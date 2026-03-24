# Demo Seed Data

The demo seed pipeline is designed to make the platform feel active and believable instead of empty.

## What it creates

- 3 realistic tenants:
  - college
  - company
  - independent learners
- 19 users total:
  - 1 platform super admin
  - 3 tenant admins
  - 3 tenant teachers
  - 3 tenant mentors
  - 9 tenant students
- 9 goals
- 54 topics
- 216 questions
- completed diagnostics for each student
- generated roadmaps with mixed completion states
- 30 days of learning activity per student
- mentor suggestions, badges, communities, threads, replies, and upvotes
- experiment records to make dashboards feel more production-like

## How to run

```bash
python seed.py
```

Docker bootstrap uses the same seed entrypoint through:

```bash
python scripts/bootstrap_seed.py
```

## Sample API responses

After seeding, generate example payloads for demos or docs:

```bash
python scripts/generate_demo_api_samples.py
```

That writes JSON samples under `docs/demo_api_samples/`.
