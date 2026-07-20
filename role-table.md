# Campus Mate — Role, Skill, Code, and Handoff Matrix

## Functional agents

| Agent | Primary responsibility | Preloaded skills | Python implementation | Main output | Handoff |
|---|---|---|---|---|---|
| `profile-manager` | Collect and validate student profile | `campus-mate-onboarding`, `profile-build` | `services/onboarding.py`, `models.UserProfile` | `data/user_profile.json` | `fit-priority` |
| `source-collector` | Discover supported notice URLs and isolate fetch failures | `source-watchlist-crawl` | `sources/linkareer.py`, `workflows/collect.py` | collection report | `multipass-parser` |
| `multipass-parser` | HTML/OCR/Vision extraction, evidence merge, review flags | `html-opportunity-parse`, `rendered-page-ocr`, `poster-vision-extract`, `schema-merge-and-validate` | `parsing/*.py`, `models.ParseCandidate` | structured `Opportunity` records | `fit-priority` |
| `fit-priority` | Explainable scoring and urgency | `interest-keyword-expand`, `fit-score-rank`, `deadline-priority-rank` | `services/recommendation.py` | score, priority, reasons | `notion-dashboard` |
| `notion-dashboard` | Non-destructive upsert and status preservation | `notion-dashboard-sync`, `accept-state-sync` | `integrations/notion.py` | page IDs, state/sync report | `schedule-notification` |
| `schedule-notification` | Slack briefing, conflict handling, accepted calendar events | `calendar-freebusy-check`, `calendar-event-create`, `slack-brief-generate`, `accept-state-sync` | `workflows/brief.py`, `conflicts.py`, `accept_sync.py`, `integrations/calendar_bridge.py` | Slack payload, calendar manifests/results | user / QA |

## Operational agents

| Agent | Trigger | Functional roles composed | Command sequence | Side effects |
|---|---|---|---|---|
| `daily-collector` | Timely 08:00 | source → parser → score → Notion → conflict | `campus-mate collect`, then optional `conflicts apply` | Notion updates |
| `slack-briefing` | Timely 09:00 | schedule-notification | `campus-mate brief` | Slack message |
| `accept-sync` | Timely hourly | notion-dashboard → schedule-notification | `calendar plan` → connector calls → `calendar apply` | Calendar + Notion status |

## Skills

| Skill | What it contributes | Side-effect level | Validation reference |
|---|---|---:|---|
| `campus-mate-orchestrator` | Phase routing, handoffs, recovery, final report | depends on mode | `workflow.md` |
| `campus-mate-onboarding` | Interactive profile dialogue | local write | `UserProfile` model |
| `campus-mate-demo` | Deterministic fixture E2E | JSON local write | fixture tests |
| `profile-build` | Profile normalization and schema validation | local write | onboarding tests |
| `source-watchlist-crawl` | Supported-source discovery contract | network read | collection report |
| `html-opportunity-parse` | Deterministic page extraction | none | parser tests |
| `rendered-page-ocr` | Optional image text recovery | local temp files | OCR test |
| `poster-vision-extract` | Optional poster field extraction | external model read | evidence contract |
| `schema-merge-and-validate` | Field precedence, confidence, conflicts | none | multipass tests |
| `interest-keyword-expand` | Conservative profile keyword expansion | none | scoring rubric |
| `fit-score-rank` | 0–100 scoring breakdown and reasons | none | recommendation tests |
| `deadline-priority-rank` | urgency labels based on deadline and fit | none | recommendation tests |
| `notion-dashboard-sync` | schema and non-destructive upsert | external write | Notion repository tests |
| `calendar-freebusy-check` | map busy intervals to opportunity conflicts | external read + local update | conflict tests |
| `calendar-event-create` | plan/apply idempotent event requests | external write bridge | calendar bridge tests |
| `accept-state-sync` | enforce state transition rules | external write | state tests |
| `slack-brief-generate` | format and optionally send briefing | external write | Slack tests |
| `qa-audit` | verify contracts, tests, secrets, artifacts | local read/write | QA checklist |

## Code-backed design principle

The Markdown harness is not decorative documentation. Each role points to executable code and measurable outputs. Conversely, the Python code does not decide the workflow policy by itself; agents and skills define when a command may run, what evidence is required, and which conditions block handoff.
