# Campus Mate Harness — Project Instructions

Campus Mate is a **code-backed Claude Code harness** for collecting university competition notices, structuring incomplete notices, scoring relevance against a student profile, and connecting approved opportunities to Notion, Slack, and Google Calendar.

The repository has two layers:

1. **Harness layer** — `.claude/agents/`, `.claude/skills/`, contracts, handoffs, validation gates, and workspace audit files.
2. **Execution layer** — the installable Python package in `src/campus_mate/`, CLI commands, integrations, tests, and Timely connector manifests.

The harness defines *who does what, when, with which evidence, and what must be true before handoff*. Python performs deterministic parsing, scoring, storage, and integration work.

## Canonical architecture

The presentation describes six functional roles. Keep those six roles visible and stable:

1. `profile-manager`
2. `source-collector`
3. `multipass-parser`
4. `fit-priority`
5. `notion-dashboard`
6. `schedule-notification`

Production automation composes those roles into three scheduled operations:

- `daily-collector` — 08:00 collection, parse, score, Notion upsert, conflict update
- `slack-briefing` — 09:00 recommendation briefing
- `accept-sync` — hourly Accept detection and calendar synchronization

The main thread runs the `campus-mate-orchestrator` skill. Subagents must not try to spawn other subagents. They return a structured handoff to the main orchestrator.

## Source of truth

- System scope and acceptance criteria: `spec.md`
- Phase ordering and recovery rules: `workflow.md`
- Agent/skill/code mapping: `role-table.md`
- Data contracts: `docs/data-contracts.md`
- Timely deployment mapping: `docs/timely-deployment.md`
- Python models: `src/campus_mate/models.py`
- State machine: `OpportunityStatus` in `src/campus_mate/models.py`

If prose and code disagree, do not silently choose one. Report the mismatch, then update both the implementation and the corresponding contract.

## Non-negotiable rules

### Evidence and parsing

- Never invent a deadline, eligibility rule, benefit, organization, or event date.
- Every parsed field must have evidence and a confidence value when the parser provides it.
- HTML/JSON-LD/Next.js state outrank OCR and vision when values conflict, unless the primary source is clearly stale or malformed.
- Unresolved conflicts become `NeedsReview`; do not guess.
- The currently complete production source adapter is Linkareer. Other sites are extension targets, not implemented claims.

### External writes

- Never delete the whole Notion database to refresh data.
- Upsert by stable `opportunity_id` or normalized source URL.
- Preserve user-controlled states: `Accept`, `Hold`, `Reject`, `Scheduled`.
- Slack is notification-only. Approval happens in Notion.
- Only `Accept` opportunities may produce calendar requests.
- Mark an opportunity `Scheduled` only after calendar results confirm success.
- Keep successful event IDs when part of a calendar batch fails; retry only failed requests.

### Security

- No secrets in source code, Markdown, fixtures, screenshots, or logs.
- Use environment variables or Timely Secrets.
- Run `python scripts/scan_secrets.py .` before packaging or committing.
- If a real token was ever committed, rotate it even after removing it from the current tree.

### Workspace and audit trail

For a harness run, use `_workspace/runs/<run-id>/` with the phase directories defined in `workflow.md`. Keep intermediate artifacts; do not overwrite unrelated runs.

A handoff is complete only when it contains:

- `status`: `PASS`, `NEEDS_REVIEW`, or `FAIL`
- input paths or identifiers
- output paths
- counts and validation summary
- warnings/errors
- recommended next agent or stop condition

### Code quality

- Python 3.11+
- Pydantic models for external and cross-phase data
- Time zone: `Asia/Seoul` unless explicitly overridden
- No fixed “today” in production code; inject dates in tests
- Network operations require timeouts and bounded retries
- Keep adapters isolated under `sources/` and integrations under `integrations/`
- Add or update tests with every behavior change

## Standard verification

Run before final sign-off:

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts
```

For a deterministic local demo:

```bash
cp examples/profile.example.json data/user_profile.json
CAMPUS_MATE_STORAGE_BACKEND=json \
  campus-mate demo --fixture examples/fixtures/linkareer_detail.html
```

## User-facing language

- Explain the system as a Timely-orchestrated, Python-backed harness.
- Distinguish the six functional agents from the three scheduled automation agents.
- Do not describe optional OCR/Vision or additional source adapters as active unless configured and demonstrated.
- Use “적합도 점수” as an explainable ranking heuristic, not an objective prediction of success.
