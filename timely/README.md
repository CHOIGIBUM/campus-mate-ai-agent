# Timely Runtime Mapping

The canonical Harness lives under `.claude/`. Timely schedules the same contracts and invokes the Python CLI plus external connectors.

## Responsibilities

- `.claude/` — reusable Agent and Skill source of truth
- `src/campus_mate/` — deterministic execution code
- `timely/automations.yaml` — schedule and connector handoff reference

## Scheduled operations

```text
08:00 daily-collector
  campus-mate collect
  optional Google Calendar free/busy query
  campus-mate conflicts apply

09:00 slack-briefing
  campus-mate brief

hourly accept-sync
  campus-mate calendar plan
  Timely/Composio Google Calendar create-event calls
  campus-mate calendar apply
```

Use Timely Secrets for credentials. Do not create a second divergent `.pi/` copy of the Agent and Skill definitions.
