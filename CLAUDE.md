# Campus Mate — Project Instructions

Campus Mate is a **code-backed Claude Code harness** that collects university competition notices, structures incomplete information, ranks relevance for a student profile, and connects user-approved opportunities to Notion, Slack, and Google Calendar.

The repository has two layers:

1. **Harness layer** — `.claude/agents/`, `.claude/skills/`, root contracts, handoffs, and hooks.
2. **Execution layer** — the Python package in `src/campus_mate/`, CLI commands, tests, and Timely connector manifests.

The harness defines who may do what, when, with which evidence, and what must be true before handoff. Python performs deterministic parsing, ranking, storage, and integration work.

## Canonical architecture

Keep these six functional agents visible and stable:

1. `profile-manager`
2. `source-collector`
3. `multipass-parser`
4. `fit-priority`
5. `notion-dashboard`
6. `schedule-notification`

Timely composes those roles into three scheduled operations:

- `daily-collector` — 08:00 collection, parsing, ranking, Notion upsert, optional conflict update
- `slack-briefing` — 09:00 recommendation briefing
- `accept-sync` — hourly Accept detection and calendar synchronization

These names are **automation schedules**, not additional Claude subagents.

The main thread runs the `campus-mate-orchestrator` Skill. Subagents return structured handoffs to the main orchestrator and must not create a competing orchestration path.

## Source of truth

- Scope and acceptance criteria: `spec.md`
- Phase order and recovery: `workflow.md`
- Agent/Skill/code mapping: `role-table.md`
- Runtime models and state machine: `src/campus_mate/models.py`
- Timely schedule mapping: `timely/automations.yaml`

If prose and code disagree, report the mismatch and update both. Do not silently choose one.

## Non-negotiable rules

### Evidence and parsing

- Never invent a deadline, eligibility rule, benefit, organization, or event date.
- Preserve field evidence, source, confidence, and warnings.
- Prefer JSON-LD, Next.js state, and visible HTML over OCR and vision unless the primary source is clearly malformed.
- Unresolved core conflicts become `NeedsReview`.
- The only complete production collection adapter is Linkareer. Other sites are extension targets.

### Recommendation

- Relevance is an explainable ranking heuristic, not a prediction of winning or acceptance.
- Keep parsing confidence separate from fit score.
- Reasons must be grounded in actual profile and notice fields.
- Missing eligibility must not be treated as eligibility.

### External writes

- Never delete or rebuild the whole Notion database for a refresh.
- Upsert by stable `opportunity_id` or normalized source URL.
- Preserve `Accept`, `Hold`, `Reject`, `Scheduling`, and `Scheduled` states.
- Slack is notification-only. Approval happens in Notion.
- Only `Accept` opportunities may produce calendar requests.
- Mark `Scheduled` only after connector results confirm success.
- Preserve successful event IDs during partial failure and retry only failed requests.

### Security

- No secrets in source, Markdown, fixtures, screenshots, logs, or handoffs.
- Use environment variables or Timely Secrets.
- Run `python scripts/scan_secrets.py .` before committing.
- Rotate any credential that was previously stored in a file, even if removed later.

### Runtime workspace

Runtime directories are generated and ignored by Git:

```text
_workspace/runs/<run-id>/
artifacts/
data/
```

A complete handoff contains:

- `status`: `PASS`, `NEEDS_REVIEW`, or `FAIL`
- input identifiers or paths
- output paths
- counts and validation summary
- warnings and errors
- recommended next agent or stop condition

### Code quality

- Python 3.11+
- Pydantic models for cross-phase and external data
- Default time zone: `Asia/Seoul`
- No fixed production date; inject dates in tests
- Bounded retries and explicit timeouts for network calls
- Source adapters under `sources/`; service connectors under `integrations/`
- Update tests with behavior changes

## Standard verification

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts .claude/hooks
ruff check src tests scripts .claude/hooks
```

## User-facing language

- Describe the project as a Timely-orchestrated, Python-backed Harness.
- Distinguish six functional agents from three scheduled automations.
- Do not claim OCR, vision, or unsupported sources are active unless configured and demonstrated.
- Use “적합도 점수” as a transparent ranking heuristic, not a probability.
