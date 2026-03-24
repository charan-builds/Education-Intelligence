# Autonomous Learning Agent

## Loop

The platform now exposes an explicit autonomous guidance loop:

1. `observe`
2. `decide`
3. `act`
4. `explain`

The implementation lives in `app/application/services/autonomous_learning_agent_service.py`.

## Observation Inputs

The agent reads:

- learner dashboard intelligence
- roadmap state
- weak topic heatmap
- due retention reviews
- long-term mentor memory
- recent learner activity
- notification candidates

## Decision Flow

The agent prioritizes decisions in this order:

1. choose a next topic if no step is active
2. schedule revision when retention is due
3. trigger a test when weakness remains ambiguous
4. send a low-friction nudge when momentum is weak
5. continue current plan when intervention is unnecessary

Each decision returns a confidence score and a human-readable `why`.

## Action System

The agent can:

- refresh and reprioritize the roadmap
- persist mentor suggestions as proactive guidance
- prepare notifications from deadline, weakness, and inactivity signals

These are surfaced through:

- `GET /mentor/agent/status`
- `POST /mentor/agent/run`

## Explainability

Every cycle returns:

- observed learner state
- decisions
- actions
- memory summary
- notifications
- cycle summary

This keeps the system inspectable instead of hiding logic behind opaque automation.
