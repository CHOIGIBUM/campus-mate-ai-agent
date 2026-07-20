# Campus Mate — System Specification

## 1. Purpose

Campus Mate reduces the repeated work required to find and manage university competitions. It collects notices, extracts structured fields, compares them with a student profile, stores recommendations in Notion, sends a Slack briefing, and creates Google Calendar events only after the user accepts an opportunity.

## 2. Product boundary

### Included

- Student profile onboarding and validation
- Linkareer notice discovery and detail retrieval
- HTML/JSON-LD/Next.js-state parsing
- Optional rendered OCR and poster vision passes
- Evidence-aware field merge and conflict detection
- Explainable relevance scoring and deadline priority
- Non-destructive Notion upsert and status preservation
- Slack recommendation briefing
- Google Calendar free/busy conflict input and event manifest output
- Timely-oriented daily/hourly runbooks
- Deterministic JSON-backed local demo and automated tests

### Not included or not claimed as complete

- Full production support for every Korean competition site
- Autonomous application submission
- Automatic decision to participate without user approval
- Guaranteed OCR/Vision availability without the required runtime and credentials
- Direct Google Calendar API calls from the Python package; production event creation is bridged through Timely/Composio manifests
- Prediction that a user will win or be accepted

## 3. Actors

| Actor | Responsibility |
|---|---|
| Student | Provides profile, reviews recommendations, changes Notion status to `Accept`, `Hold`, or `Reject` |
| Claude Code main thread | Runs the orchestrator skill and delegates bounded tasks to subagents |
| Functional agents | Apply domain-specific contracts and verify phase outputs |
| Timely | Executes scheduled prompts/scripts and connector operations |
| Notion | Stores the single operational dashboard and approval state |
| Slack | Receives one-way recommendation briefings |
| Google Calendar | Stores approved deadline, preparation, and event dates |

## 4. Functional requirements

### Profile

- **FR-P01** Collect school, grade, major, and at least one interest.
- **FR-P02** Never fill missing required fields with invented defaults.
- **FR-P03** Normalize comma-separated lists and remove duplicates.
- **FR-P04** Persist a validated `UserProfile` JSON document.

### Collection

- **FR-C01** Discover up to the configured limit from a supported source.
- **FR-C02** Normalize URLs and derive a stable opportunity identifier.
- **FR-C03** Isolate one failed notice from the rest of the run.
- **FR-C04** Record discovered/stored/failure counts.

### Multi-pass parsing

- **FR-M01** Parse deterministic web sources first: JSON-LD, Next.js data, and visible HTML.
- **FR-M02** Run OCR or vision only when enabled and useful, unless `--all-passes` is requested.
- **FR-M03** Record evidence source, excerpt, and confidence per field.
- **FR-M04** Mark contradictory or insufficient core fields for review.
- **FR-M05** Never infer an unsupported date or eligibility criterion.

### Recommendation

- **FR-R01** Produce a 0–100 heuristic score with a category breakdown.
- **FR-R02** Generate human-readable reasons grounded in the profile and notice text.
- **FR-R03** Assign `긴급`, `중요`, or `참고` using relevance and deadline rules.
- **FR-R04** Keep parsing confidence separate from recommendation score.

### Notion

- **FR-N01** Ensure required properties without deleting existing pages.
- **FR-N02** Upsert by stable ID or source URL.
- **FR-N03** Preserve user-controlled terminal/intermediate states.
- **FR-N04** Preserve manual notes and calendar event IDs.
- **FR-N05** Store parse warnings and sync errors visibly.

### Slack

- **FR-S01** Sort recommendations by priority, score, and deadline.
- **FR-S02** Include deadline, score, reason, conflict status, and Notion link where available.
- **FR-S03** Support dry-run payload generation.
- **FR-S04** Slack must not be used as the approval source of truth.

### Calendar and approval

- **FR-G01** Only `Accept` items may enter calendar planning.
- **FR-G02** Generate up to three event kinds: deadline, D-3 preparation, and event/start.
- **FR-G03** Attach stable request and idempotency identifiers.
- **FR-G04** Apply success/failure per event, not per batch.
- **FR-G05** Transition to `Scheduled` only when required event creation succeeds.
- **FR-G06** Keep failed items in a recoverable state such as `CalendarError`.

## 5. State machine

```text
New
  ↓ parse + score complete
Recommended
  ├─ user → Accept → Scheduling → Scheduled
  ├─ user → Hold
  └─ user → Reject

Parsing ambiguity → NeedsReview
Calendar failure → CalendarError → retry → Scheduling/Scheduled
```

Rules:

- `Accept`, `Hold`, `Reject`, and `Scheduled` must not be overwritten by routine collection.
- `NeedsReview` is not automatically promotable without resolving required fields.
- Re-running collection must not create duplicate Notion pages.
- Re-running calendar planning must not create duplicate event requests for already stored event IDs.

## 6. Core data contracts

Canonical Pydantic models are in `src/campus_mate/models.py`. Human-readable contracts and examples are in `docs/data-contracts.md`.

Required notice fields for a normal recommendation:

- `source`
- `source_url`
- `title`
- stable `opportunity_id`

High-value but nullable fields:

- organization
- deadline
- eligibility
- submission
- benefits
- event date
- poster URL

A missing deadline does not permit invention. It lowers completeness and can trigger `NeedsReview`.

## 7. Non-functional requirements

- **NFR-01 Security:** no plaintext secrets; secret scanner passes.
- **NFR-02 Idempotency:** repeat runs do not duplicate Notion pages or calendar events.
- **NFR-03 Auditability:** phase artifacts and handoffs are preserved.
- **NFR-04 Explainability:** recommendation reasons and parse evidence are inspectable.
- **NFR-05 Resilience:** one bad notice does not abort the whole collection run.
- **NFR-06 Testability:** JSON backend and fixtures permit external-service-free tests.
- **NFR-07 Portability:** core logic is Python and does not depend on one LLM runtime.
- **NFR-08 Runtime integration:** Timely supplies schedules and connector execution; Claude Code supplies the reusable harness and subagent coordination.

## 8. Completion criteria

A full end-to-end run is complete when:

1. A validated profile exists.
2. At least one notice is discovered or the run records a valid zero-result outcome.
3. Each stored notice has parse evidence and a recommendation or `NeedsReview` status.
4. Notion upsert is non-destructive.
5. A Slack dry-run or delivery report exists.
6. Accepted items produce calendar request manifests.
7. Calendar results are applied per request.
8. No duplicate page or event is created on a repeated run.
9. Tests, harness validation, and secret scan pass.
