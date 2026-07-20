# Campus Mate — Workflow and Handoff Protocol

## 1. Run modes

| Mode | Trigger examples | External writes | Phases |
|---|---|---:|---|
| `onboard` | “온보딩 시작”, “프로필 설정” | profile file only | 0–1 |
| `demo` | “시연 시작”, `/campus-mate-demo` | JSON backend by default | 0–8 |
| `daily` | 08:00 Timely automation | Notion; conflict updates | 0–6, 8 |
| `brief` | 09:00 Timely automation | Slack | 0, 6, 8 |
| `accept-sync` | hourly Timely automation | Calendar and Notion state | 0, 7, 8 |
| `partial` | “파싱만 다시”, “브리핑만 다시” | phase-specific | affected phase + downstream validation |
| `recovery` | retry after `NeedsReview`/`CalendarError` | controlled | failed request only |

## 2. Workspace layout

Every orchestrated run should write an audit trail under a unique directory:

```text
_workspace/runs/<YYYYMMDD-HHMMSS>-<mode>/
├── manifest.json
├── 00_input/
│   ├── request.md
│   └── profile.snapshot.json
├── 01_collection/
│   ├── discovered-urls.json
│   └── collection-report.json
├── 02_parsing/
│   ├── opportunities.json
│   └── parse-review.md
├── 03_recommendation/
│   ├── scored-opportunities.json
│   └── score-review.md
├── 04_notion/
│   └── notion-sync-report.json
├── 05_briefing/
│   └── slack-payload.json
├── 06_calendar/
│   ├── freebusy.json
│   ├── calendar-requests.json
│   └── calendar-results.json
├── 07_qa/
│   └── qa-report.md
└── handoffs/
    ├── profile-manager.json
    ├── source-collector.json
    └── ...
```

The Python package may also write to `data/` and `artifacts/`. The workspace stores run-level copies and review notes, not a competing source of truth.

## 3. Handoff envelope

Every functional agent returns a JSON-compatible handoff:

```json
{
  "agent": "multipass-parser",
  "status": "PASS",
  "inputs": ["_workspace/.../discovered-urls.json"],
  "outputs": ["_workspace/.../opportunities.json"],
  "metrics": {"parsed": 8, "needs_review": 1},
  "warnings": ["one notice had conflicting deadlines"],
  "errors": [],
  "next": "fit-priority"
}
```

Allowed `status` values:

- `PASS` — downstream phase may continue
- `NEEDS_REVIEW` — safe partial output exists; human or targeted rerun required
- `FAIL` — no safe downstream use

## 4. End-to-end phases

### Phase 0 — Context and safety

1. Determine mode from user request or Timely schedule.
2. Create a unique run directory and `manifest.json`.
3. Read `CLAUDE.md`, `spec.md`, and the relevant skill.
4. Confirm storage backend and external-write intent.
5. Check that no secret value is being copied into artifacts.

Stop conditions:

- Missing required environment variables for a requested external write
- Attempt to use an unsupported source as if it were production-ready
- User asks for destructive Notion replacement

### Phase 1 — Profile

Lead agent: `profile-manager`

1. Load existing profile if present.
2. Ask only for missing required fields.
3. Normalize and validate with `UserProfile`.
4. Save profile and snapshot it into the run workspace.
5. Produce a concise confirmation summary.

Gate:

- school, grade, major, and at least one interest exist
- no invented data

### Phase 2 — Collection

Lead agent: `source-collector`

1. Use the supported source adapter.
2. Discover up to configured limit.
3. Normalize and deduplicate URLs.
4. Fetch details with timeout and bounded retries.
5. Record per-item success/failure.

Gate:

- discovery report exists even for zero results
- no login bypass or terms-violating workaround

### Phase 3 — Multi-pass parsing

Lead agent: `multipass-parser`

1. Extract deterministic data from JSON-LD, Next.js state, and HTML.
2. Evaluate missing high-value fields.
3. If enabled/useful, run rendered OCR.
4. If enabled/useful, run poster vision.
5. Merge by field with evidence and confidence.
6. Record conflicts and `NeedsReview` conditions.

Gate:

- every stored opportunity has title, source URL, stable ID
- no unsupported inference
- conflicts are explicit

### Phase 4 — Relevance and priority

Lead agent: `fit-priority`

1. Expand profile and notice keywords conservatively.
2. Compute scoring breakdown.
3. Compute deadline priority.
4. Generate grounded reasons.
5. Keep score separate from eligibility certainty and parse confidence.

Gate:

- score in 0–100
- breakdown sums to score
- reasons cite observed profile/notice attributes

### Phase 5 — Notion and conflicts

Lead agent: `notion-dashboard`

1. Ensure schema without deletion.
2. Upsert by stable ID/URL.
3. Preserve manual states and notes.
4. If free/busy input exists, apply conflict status.
5. Record Notion page IDs and sync errors.

Gate:

- repeat run does not create duplicate page
- user state is preserved

### Phase 6 — Briefing

Lead agent: `schedule-notification`
Operational wrapper: `slack-briefing`

1. Query recommended items.
2. Sort by urgency, score, deadline.
3. Generate Slack Block Kit payload.
4. Default to dry-run in an interactive Claude Code session unless the user explicitly requests delivery.
5. In scheduled Timely mode, deliver to configured channel.

Gate:

- destination channel ID is configured for delivery
- payload contains no tokens or private profile fields

### Phase 7 — Accept and calendar

Lead agent: `schedule-notification`
Operational wrapper: `accept-sync`

1. Query only `Accept` items.
2. Plan deadline/preparation/event requests.
3. Assign request and idempotency IDs.
4. Timely/Composio creates events.
5. Apply result file per request.
6. Store event IDs and transition successful opportunities.
7. Keep failed items recoverable.

Gate:

- no event for non-Accept items
- no `Scheduled` without confirmed result
- repeat run skips already-created event kinds

### Phase 8 — QA and report

Skill: `qa-audit`

1. Verify phase artifacts and handoffs.
2. Check state transitions and duplicate prevention.
3. Run tests, harness validator, and secret scan when code changed.
4. Write `07_qa/qa-report.md`.
5. Summarize completed actions, skipped optional passes, warnings, and follow-up.

## 5. Partial reruns

- Profile changed → rerun recommendation, Notion, briefing; do not recollect unless requested.
- Parser improved → rerun parsing for affected URLs, then recommendation and Notion.
- Score rule changed → rerun recommendation onward.
- Slack formatting changed → rerun briefing only.
- Calendar failure → rerun failed requests only.
- A user changes `Hold`/`Reject` → do not create calendar events; no other phase required.

## 6. Recovery rules

| Failure | Recovery |
|---|---|
| One source URL fails | Continue other URLs; report item failure |
| OCR unavailable | Record skipped pass; use HTML/vision evidence |
| Vision unavailable | Record skipped pass; never fabricate missing fields |
| Conflicting deadline | `NeedsReview`; block automatic scheduling |
| Notion rate limit | bounded retry, then sync error without deleting data |
| Slack delivery fails | keep dry-run artifact and delivery error |
| One calendar request fails | preserve successful IDs; retry failed request only |
| Secret detected | block write/commit; rotate if exposure occurred |

## 7. Final run summary

The orchestrator reports:

- run ID and mode
- profile status
- discovered, parsed, recommended, review, and failure counts
- Notion upsert counts
- Slack dry-run/delivery result
- calendar request/success/failure counts
- QA status
- exact artifact paths
