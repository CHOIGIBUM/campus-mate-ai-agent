# Timely Deployment Guide

## Runtime split

- Claude Code uses `.claude/` to discover the reusable harness.
- Timely runs scheduled prompts, Python commands, and external connectors.
- The Python package contains deterministic logic shared by both environments.

## Secrets

Set these in Timely Secrets or an uncommitted `.env`:

```dotenv
CAMPUS_MATE_STORAGE_BACKEND=notion
NOTION_API_KEY=
NOTION_DATA_SOURCE_ID=
NOTION_DASHBOARD_URL=
SLACK_BOT_TOKEN=
SLACK_CHANNEL_ID=
CAMPUS_MATE_VISION_API_KEY=
CAMPUS_MATE_VISION_MODEL=
```

Never paste secret values into agent Markdown or prompt text.

## Scheduled operations

### Daily collector — 08:00 KST

```bash
campus-mate collect --source linkareer --limit 8 \
  --report artifacts/daily-collection.json
```

Then Timely may query Google Calendar free/busy, save the normalized response, and run:

```bash
campus-mate conflicts apply --input artifacts/freebusy.json
```

### Slack briefing — 09:00 KST

```bash
campus-mate brief
```

Use `--dry-run --output artifacts/slack-briefing.json` during setup.

### Accept sync — hourly

```bash
campus-mate calendar plan --output artifacts/calendar-requests.json
```

Timely/Composio creates each event, preserving `request_id`, and writes `artifacts/calendar-results.json`.

```bash
campus-mate calendar apply \
  --requests artifacts/calendar-requests.json \
  --results artifacts/calendar-results.json
```

## Connector rules

- Slack is one-way notification; do not treat reactions or buttons as approval.
- Notion status is the approval source of truth.
- Google Calendar creation must return an event ID before the corresponding status becomes `Scheduled`.
- Use a dedicated test calendar or hide unrelated personal events in demo screenshots.

## Timely reference manifest

`timely/automations.yaml` documents the intended schedule and command mapping. It is a portable reference, not a guarantee that every Timely account can import YAML directly.
