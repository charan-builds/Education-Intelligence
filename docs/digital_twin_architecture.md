# Digital Twin Architecture

## Goal

Create a virtual representation of each learner that models:

- strengths
- weaknesses
- learning speed
- memory retention
- behavior patterns
- likely future performance

## Core Design

The first version is a computed digital twin, not a separately persisted twin state machine.

It assembles current learner state from existing platform signals:

- roadmap progression
- topic scores
- retention data
- learning events
- ML feature snapshots
- predictive risk logic

## Twin Layers

### 1. Current Model

Represents the learner now:

- strongest and weakest topics
- learning speed
- retention score
- session cadence
- engagement pattern
- learning profile

### 2. Simulation Layer

Uses the learning simulation engine to project:

- baseline progress
- accelerated focus strategy
- retention-first strategy

Each strategy estimates:

- completion date
- progress curve
- readiness gain
- retention gain

### 3. Decision Support

Compares strategies and recommends:

- best strategy
- next learning path
- rationale for the recommendation

## Repo Mapping

- service: `app/application/services/digital_twin_service.py`
- route: `app/presentation/digital_twin_routes.py`
- schema: `app/schemas/digital_twin_schema.py`
- frontend page: `learning-platform-frontend/app/(student)/student/digital-twin/page.tsx`

## Why This Works

This approach avoids duplicating learner state while still producing a coherent twin:

- current platform signals provide the observed learner
- simulation provides future-state hypotheses
- predictive intelligence provides risk
- decision support chooses the best path among alternatives
