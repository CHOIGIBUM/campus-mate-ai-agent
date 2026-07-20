# Campus Mate — System Specification

## 1. Purpose

Campus Mate reduces the repeated work required to find and manage university competitions. It collects notices, structures key fields, compares them with a student profile, stores recommendations in Notion, sends a Slack briefing, and creates Google Calendar events only after explicit user approval.

## 2. Product boundary

### Included

- Student profile onboarding and validation
- Linkareer notice discovery and detail retrieval
- HTML, JSON-LD, and Next.js-state parsing
- Optional rendered OCR and poster vision passes
- Evidence-aware field merge and conflict detection
- Explainable relevance scoring and deadline priority
- Non-destructive Notion upsert and state preservation
- Slack recommendation briefing
- Google Calendar free/busy input and event request/result bridge
- Timely daily and hourly automation mapping
- Deterministic JSON-backed fixture demo and automated tests

### Not claimed as complete

- Full production support for every Korean competition site
- Autonomous application submission
- Automatic participation decisions without user approval
- Guaranteed OCR or vision without the required runtime and credentials
- Direct Google Calendar creation inside the Python package; production event creation is bridged through Timely/Composio
- Prediction that a user will win or be accepted

## 3. Actors and systems

| Actor or system | Responsibility |
|---|---|
| Student | Provides profile, reviews recommendations, selects `Accept`, `Hold`, or `Reject` in Notion |
| Claude Code main thread | Runs the orchestrator and delegates bounded tasks to six agents |
| Functional agents | Apply domain contracts and verify phase outputs |
| Timely | Executes schedules, Python commands, and connector operations |
| Notion | Operational dashboard and approval source of truth |
| Slack | One-way recommendation briefing |
| Google Calendar | Approved deadline, preparation, and event schedules |

## 4. Functional requirements

### Profile

- **FR-P01** Collect school, grade, major, and at least one interest.
- **FR-P02** Never fill missing required fields with invented defaults.
- **FR-P03** Normalize comma-separated lists and remove duplicates.
- **FR-P04** Persist a validated `UserProfile` JSON document.
- **FR-P05** Avoid collecting unnecessary sensitive personal data.

### Collection

- **FR-C01** Discover up to the configured limit from a supported source.
- **FR-C02** Normalize URLs and derive a stable opportunity identifier.
- **FR-C03** Isolate one failed notice from the rest of the run.
- **FR-C04** Record discovered, parsed, stored, review, and failure counts.
- **FR-C05** Never present an unimplemented source adapter as production support.

### Multi-pass parsing

- **FR-M01** Parse deterministic sources first: JSON-LD, Next.js data, and visible HTML.
- **FR-M02** Run OCR or vision only when enabled and useful, unless an explicit all-pass test is requested.
- **FR-M03** Record evidence source, excerpt, and confidence per field.
- **FR-M04** Mark contradictory or insufficient core fields for review.
- **FR-M05** Never infer an unsupported date or eligibility criterion.
- **FR-M06** Block automatic scheduling when a core date conflict remains unresolved.

### Recommendation

- **FR-R01** Produce a 0–100 heuristic score with category breakdown.
- **FR-R02** Generate reasons grounded in the profile and notice text.
- **FR-R03** Assign `긴급`, `중요`, or `참고` using relevance and deadline rules.
- **FR-R04** Keep parsing confidence separate from recommendation score.
- **FR-R05** Do not present the score as a probability of success.

### Notion

- **FR-N01** Ensure required properties without deleting existing pages.
- **FR-N02** Upsert by stable ID or source URL.
- **FR-N03** Preserve user-controlled states and manual notes.
- **FR-N04** Preserve calendar event IDs and successful partial results.
- **FR-N05** Store parse warnings and sync errors visibly.

### Slack

- **FR-S01** Sort recommendations by priority, score, and deadline.
- **FR-S02** Include deadline, score, reasons, conflict status, and Notion link where available.
- **FR-S03** Support dry-run payload generation.
- **FR-S04** Never treat a Slack interaction as participation approval.

### Calendar and approval

- **FR-G01** Only `Accept` items may enter calendar planning.
- **FR-G02** Generate up to three event kinds: deadline, D-3 preparation, and event/start.
- **FR-G03** Attach stable request and idempotency identifiers.
- **FR-G04** Apply success and failure per event, not per batch.
- **FR-G05** Transition to `Scheduled` only after required event creation succeeds.
- **FR-G06** Keep failed items in a recoverable state such as `CalendarError`.
- **FR-G07** Re-running the same synchronization must not duplicate existing event kinds.

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

Routine collection must not move user-controlled states backwards.

## 6. Data contracts

Canonical Pydantic models are defined in `src/campus_mate/models.py`.

Core cross-phase objects:

- `UserProfile`
- `SourcePage`
- `ParseCandidate`
- `FieldEvidence`
- `Opportunity`
- `Recommendation`
- `CalendarEventRequest`
- `CalendarEventResult`
- `WorkflowReport`

Safe example files are under `examples/`. Runtime `data/`, `artifacts/`, and `_workspace/` are generated locally and ignored by Git.

## 7. Non-functional requirements

### Safety and privacy

- Secrets come only from environment variables or Timely Secrets.
- Runtime profile and schedule data are excluded from Git.
- Logs and handoffs must not contain token values.
- Hooks and CI scan common credential patterns.

### Reliability

- Network operations use explicit timeouts and bounded retries.
- One item failure must not abort unrelated items.
- Upserts and calendar requests are idempotent.
- Partial success must be preserved.

### Explainability

- Parsed fields retain evidence and confidence.
- Recommendation reasons identify matched profile and notice attributes.
- Review states explain why automatic processing stopped.

### Maintainability

- Six Agent definitions remain the stable functional architecture.
- Twelve Skill definitions remain the stable method contracts.
- Python code is organized by source, parsing, service, integration, and workflow layers.
- Contract and behavior changes require tests or explicit validation updates.

## 8. Acceptance scenarios

### A. Fixture demo

1. Import the example profile.
2. Parse the fixture notice.
3. Produce evidence-aware structured fields.
4. Compute score, priority, and reasons.
5. Store through the JSON backend.
6. Re-run without creating a duplicate.

### B. Live daily collection

1. Timely starts `daily-collector` at 08:00.
2. Linkareer notices are discovered and parsed.
3. Recommendations are calculated.
4. Notion pages are created or updated without destructive refresh.
5. Optional free/busy input updates conflict status.

### C. Briefing

1. Timely starts `slack-briefing` at 09:00.
2. Recommended items are sorted and formatted.
3. Dry-run is available for review.
4. Configured delivery posts one Slack briefing.

### D. Approval and scheduling

1. The user changes a Notion item to `Accept`.
2. `accept-sync` creates an idempotent request manifest.
3. Timely/Composio creates calendar events.
4. Python applies results by request ID.
5. Confirmed items become `Scheduled`; failures remain recoverable.

## 9. Definition of done

A release is complete when:

- Harness validation passes with 6 agents and 12 skills.
- Unit tests, lint, compile, and secret scan pass.
- Fixture demo completes without duplicate storage.
- No presentation file, live token, runtime profile, personal schedule, or execution log is committed.
- README accurately separates implemented, optional, and unsupported capabilities.
