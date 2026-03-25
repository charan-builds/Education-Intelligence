# Multi-Agent AI Architecture

## Goal

Move from a single generic AI response path to a collaborative agent team with specialization.

## Agent Set

- `mentor_agent`
- `content_generator_agent`
- `analytics_agent`
- `career_advisor_agent`
- `motivation_agent`

## Responsibilities

### Mentor Agent

- core tutoring voice
- prioritization
- study guidance synthesis

### Content Generator Agent

- explanations
- practice material
- follow-up exercises

### Analytics Agent

- progress interpretation
- weak-signal diagnosis
- measurement framing

### Career Advisor Agent

- role relevance
- job-readiness framing
- resume/interview alignment

### Motivation Agent

- momentum recovery
- habit reinforcement
- tone adjustment when progress is weak

## Orchestration Flow

1. receive learner request
2. build shared learner context
3. route to specialist agents based on message intent and learner state
4. collect specialist summaries and recommendations
5. synthesize a single learner-facing reply
6. return collaboration metadata for explainability

## Routing Heuristics

Examples:

- explanation / quiz / practice -> content generator
- weak progress / low completion / stuck signals -> analytics
- interview / resume / job / role -> career advisor
- low completion / focus / burnout / motivation -> motivation
- mentor agent is always included

## Explainability

The orchestrator now returns:

- routed agents
- orchestrator summary
- per-agent outputs

This preserves a simple frontend reply while keeping the system inspectable.

## Current Repo Mapping

- orchestration logic: `ai_service/service.py`
- specialist and synthesis prompts: `ai_service/prompts.py`
- collaboration schema: `ai_service/schemas.py`
- current entrypoint: `POST /ai/mentor-chat`
