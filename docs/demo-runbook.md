# Campus Mate Demo Runbook

## Goal

Demonstrate collection → structure → recommendation → Notion → Slack → user Accept → Google Calendar without claiming unsupported sources or hidden manual steps.

## Before the demo

1. Rotate and configure Notion/Slack credentials.
2. Share the Notion database with the integration.
3. Use a test Slack channel and test Google Calendar.
4. Run `campus-mate --storage notion notion ensure-schema`.
5. Complete the profile with `/campus-mate-onboarding` or `campus-mate profile init`.
6. Dry-run the briefing and calendar manifests.
7. Run all verification commands.

## Seven-minute sequence

1. **Problem (30 sec)** — notices are fragmented and deadlines are managed separately.
2. **Harness (45 sec)** — six functional agents, code-backed skills, Timely schedules.
3. **Start (30 sec)** — invoke `/campus-mate-demo live` or the Timely “시연 시작” trigger.
4. **Notion (90 sec)** — show title, poster, deadline, eligibility, score, reason, state, conflict.
5. **Slack (45 sec)** — show actual `#공모전브리핑` message.
6. **Accept (30 sec)** — change one Notion item to `Accept`.
7. **Calendar (60 sec)** — run accept sync and show deadline/D-3/event entries.
8. **Reliability (45 sec)** — rerun and show no duplicate page/event; mention evidence and review state.
9. **Close (30 sec)** — summarize role and finalist result.

## Screenshot set for README

- Timely runtime/automation panel
- Notion dashboard with real structured rows
- Notion `Accept` → `Scheduled` state
- Slack briefing result
- Google Calendar generated events

Remove tokens, personal calendar titles, browser profile data, and unrelated workspace information.
