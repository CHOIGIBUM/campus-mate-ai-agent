# Campus Mate — Agent, Skill, Code, and Handoff Matrix

## 1. Functional agents

| Agent | Primary responsibility | Skills | Python implementation | Main output | Handoff |
|---|---|---|---|---|---|
| `profile-manager` | Collect, normalize, and validate the student profile | `profile-build` | `services/onboarding.py`, `services/keywords.py`, `models.UserProfile` | validated profile and search terms | `fit-priority` |
| `source-collector` | Discover supported notice URLs and isolate failures | `source-watchlist-crawl` | `sources/linkareer.py`, `workflows/collect.py` | collection report | `multipass-parser` |
| `multipass-parser` | HTML/OCR/Vision extraction, evidence merge, review flags | `html-opportunity-parse`, `rendered-page-ocr`, `poster-vision-extract`, `schema-merge-and-validate` | `parsing/*.py`, `models.ParseCandidate` | structured `Opportunity` records | `fit-priority` |
| `fit-priority` | Explainable relevance, urgency, and recommendation reasons | `recommendation-rank` | `services/recommendation.py`, `services/keywords.py` | score, priority, reasons | `notion-dashboard` |
| `notion-dashboard` | Non-destructive upsert and state preservation | `notion-dashboard-sync` | `integrations/notion.py` | page IDs and sync report | `schedule-notification` |
| `schedule-notification` | Conflict status, Slack briefing, Accept-only calendar synchronization | `slack-brief-generate`, `calendar-sync` | `workflows/brief.py`, `conflicts.py`, `accept_sync.py`, `integrations/calendar_bridge.py` | briefing and calendar artifacts | user / QA |

## 2. Timely scheduled operations

| Automation | Trigger | Functional roles composed | Command flow | Side effects |
|---|---|---|---|---|
| `daily-collector` | 08:00 daily | source → parser → rank → Notion → optional conflict | `campus-mate collect`, optional `conflicts apply` | Notion updates |
| `slack-briefing` | 09:00 daily | schedule-notification | `campus-mate brief` | Slack message |
| `accept-sync` | hourly | Notion read → schedule-notification | `calendar plan` → connector → `calendar apply` | Calendar and Notion status |

These are deployment schedules, not additional Agent definitions.

## 3. Skills

| Skill | Contribution | Side-effect level | Main executable mapping |
|---|---|---:|---|
| `campus-mate-orchestrator` | Mode routing, Agent delegation, handoffs, recovery, final report | depends on mode | CLI and six Agents |
| `profile-build` | Interactive onboarding, profile validation, conservative search-term generation | local write | `campus-mate profile ...`, `services/onboarding.py` |
| `source-watchlist-crawl` | Supported-source discovery and URL contract | network read | `campus-mate-skill source-watchlist-crawl` |
| `html-opportunity-parse` | Deterministic page extraction | none | `campus-mate-skill html-opportunity-parse` |
| `rendered-page-ocr` | Optional rendered text recovery | local temp/network read | `campus-mate-skill rendered-page-ocr` |
| `poster-vision-extract` | Optional poster field extraction | external model read | `campus-mate-skill poster-vision-extract` |
| `schema-merge-and-validate` | Field precedence, evidence, confidence, conflict detection | none | `campus-mate-skill schema-merge-and-validate` |
| `recommendation-rank` | Keyword expansion, 0–100 breakdown, priority, reasons | none | `interest-keyword-expand`, `fit-score-rank`, `deadline-priority-rank` CLI actions |
| `notion-dashboard-sync` | Schema and non-destructive upsert | external write | `integrations/notion.py` |
| `slack-brief-generate` | Format and optionally send the briefing | external write | `campus-mate brief`, `workflows/brief.py` |
| `calendar-sync` | Free/busy, Accept state, idempotent requests, result application | external read/write bridge | `conflicts apply`, `calendar plan/apply` |
| `qa-audit` | Contract, state, test, secret, and artifact verification | local read/write | `validate_harness.py`, tests, secret scan |

## 4. Code-backed design principle

The Markdown harness is not decorative documentation. Each role points to executable code and measurable outputs. Conversely, Python does not decide workflow policy by itself; Agent and Skill contracts determine when a command may run, what evidence is required, which states are protected, and which conditions block handoff.
