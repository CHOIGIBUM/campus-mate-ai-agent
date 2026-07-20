# Campus Mate — Orchestration Workflow

## 1. Run modes

| Mode | Typical trigger | External write | Phases |
|---|---|---:|---|
| `status` | configuration or repository inspection | no | 0, 8 |
| `onboard` | new profile or profile update | local profile only | 0, 1, 8 |
| `demo` | fixture demo or explicitly approved live demo | JSON by default | 0–8 |
| `daily` | Timely `daily-collector` or manual collection | Notion when configured | 0–5, 8 |
| `brief` | Timely `slack-briefing` or manual briefing | Slack when approved | 0, 6, 8 |
| `accept-sync` | Timely hourly schedule or manual approval sync | Calendar and Notion | 0, 7, 8 |
| `partial:<phase>` | targeted recovery | depends on phase | required phase and downstream |

If external-write intent is unclear, begin with `status` or dry-run.

## 2. Runtime workspace

Each orchestrated run creates:

```text
_workspace/runs/<timestamp>-<mode>/
├── manifest.json
├── 00_input/
├── 01_profile/
├── 02_collection/
├── 03_parsing/
├── 04_recommendation/
├── 05_notion/
├── 06_notification/
├── 07_calendar/
├── 08_qa/
└── handoffs/
```

The runtime directory is intentionally ignored by Git.

## 3. Handoff contract

```json
{
  "status": "PASS",
  "agent": "multipass-parser",
  "inputs": ["02_collection/source-pages.json"],
  "outputs": ["03_parsing/opportunities.json"],
  "metrics": {"parsed": 8, "needs_review": 1},
  "warnings": ["one notice had conflicting deadlines"],
  "errors": [],
  "next": "fit-priority"
}
```

Allowed `status` values:

- `PASS` — downstream may continue.
- `NEEDS_REVIEW` — safe partial output exists, but targeted review is required.
- `FAIL` — no safe downstream use.

## 4. End-to-end phases

### Phase 0 — Context and safety

1. Determine mode from the user request or Timely schedule.
2. Read `CLAUDE.md`, `spec.md`, and relevant Skills.
3. Create a run directory and manifest.
4. Check profile, storage backend, optional OCR/Vision, and credential presence without printing secrets.
5. Determine whether external write is allowed.

Stop when required configuration is missing for a requested write, an unsupported source is requested as production-ready, or a destructive Notion refresh is proposed.

### Phase 1 — Profile

Lead Agent: `profile-manager`

1. Load the current profile if present.
2. Ask only for missing or intentionally changed values.
3. Normalize and validate with `UserProfile`.
4. Save the profile and a run snapshot.
5. Return search terms and changed fields.

Gate: school, grade, major, and at least one interest exist; no invented values.

### Phase 2 — Collection

Lead Agent: `source-collector`

1. Confirm a supported source adapter.
2. Discover up to the configured limit.
3. Normalize and deduplicate URLs.
4. Fetch with timeout and bounded retries.
5. Record per-item success and failure.

Gate: a collection report exists even when zero notices are found.

### Phase 3 — Multi-pass parsing

Lead Agent: `multipass-parser`

1. Parse JSON-LD, Next.js state, and visible HTML.
2. Evaluate missing or conflicting high-value fields.
3. Run rendered OCR only when enabled and useful.
4. Run poster vision only when enabled and useful.
5. Merge by field with evidence, confidence, and warnings.
6. Mark unresolved core conflicts as `NeedsReview`.

Gate: every stored item has title, source URL, stable ID, and explicit review state.

### Phase 4 — Relevance and priority

Lead Agent: `fit-priority`

1. Build conservative profile search terms.
2. Compute score breakdown.
3. Compute deadline priority.
4. Generate grounded reasons.
5. Preserve uncertainty around eligibility and parsing.

Gate: score is 0–100, breakdown sums to score, and reasons cite observed attributes.

### Phase 5 — Notion and conflict status

Lead Agent: `notion-dashboard`

1. Ensure required schema without deletion.
2. Upsert by stable ID or source URL.
3. Preserve manual states, notes, and calendar IDs.
4. If normalized free/busy input exists, apply conflict status.
5. Record page IDs and sync errors.

Gate: repeat runs keep the same page and preserve user state.

### Phase 6 — Slack briefing

Lead Agent: `schedule-notification`

1. Query `Recommended` items.
2. Sort by priority, score, and deadline.
3. Create the Slack payload.
4. Default to dry-run in an interactive session unless delivery is explicitly requested.
5. Timely scheduled mode may deliver to the configured channel.

Gate: no token or private profile field appears in the payload.

### Phase 7 — Accept and calendar

Lead Agent: `schedule-notification`

1. Query only `Accept` items.
2. Plan deadline, preparation, and event requests.
3. Attach stable request and idempotency IDs.
4. Timely/Composio creates events.
5. Apply results per request ID.
6. Preserve successful event IDs and retry only failures.
7. Transition to `Scheduled` only after confirmed success.

Gate: no event request for a non-Accept item and no unconfirmed `Scheduled` state.

### Phase 8 — QA and report

Skill: `qa-audit`

1. Verify phase artifacts and handoffs.
2. Check state transitions and duplicate prevention.
3. Run tests, harness validator, compile, lint, and secret scan when code changed.
4. Summarize actions, skipped optional passes, warnings, and follow-up.

## 5. Timely schedule composition

```text
08:00 daily-collector
  source-collector
  → multipass-parser
  → fit-priority
  → notion-dashboard
  → optional schedule-notification conflict update

09:00 slack-briefing
  schedule-notification

hourly accept-sync
  notion-dashboard read
  → schedule-notification calendar plan/apply
```

The schedule names are deployment units, not additional `.claude/agents`.

## 6. Partial reruns

- Profile changed → recommendation, Notion, and briefing; no recollection unless requested.
- Parser improved → affected URLs only, then recommendation and Notion.
- Ranking rule changed → recommendation onward.
- Slack format changed → briefing only.
- Calendar failure → failed requests only.
- User changes to `Hold` or `Reject` → no calendar event; no earlier phase required.

## 7. Recovery rules

| Failure | Recovery |
|---|---|
| One source URL fails | Continue other URLs and record item failure |
| OCR unavailable | Record skipped pass and keep HTML/vision evidence |
| Vision unavailable | Record skipped pass and never fabricate fields |
| Conflicting deadline | `NeedsReview`; block automatic scheduling |
| Notion rate limit | Bounded retry, then sync error without deletion |
| Slack delivery failure | Preserve dry-run payload and error |
| One calendar request fails | Preserve successful IDs and retry failed request only |
| Secret detected | Block write/commit and rotate exposed credential |

## 8. Final run summary

The orchestrator reports:

- run ID and mode
- agents invoked
- discovered, parsed, recommended, review, and failure counts
- Notion create/update/preserve counts
- Slack dry-run or delivery result
- calendar request/success/failure counts
- QA status
- exact artifact paths and warnings
