<div align="center">

<img src="./assets/overview/campus-mate.png" width="100%" alt="Campus Mate multi-agent workflow overview" />

# Campus Mate Harness

**A code-backed Claude Code harness that structures fragmented university competition notices,<br/>ranks them against a student profile, and connects Notion approval to Slack briefings and Google Calendar.**

<p>
  <a href="./README.md">한국어</a> · <strong>English</strong>
</p>

![Harness](https://img.shields.io/badge/Harness-Claude%20Code-6D5CE7)
![Agents](https://img.shields.io/badge/Agents-6%20Functional%20%2B%203%20Operational-0C4F5A)
![Skills](https://img.shields.io/badge/Skills-18-147C8A)
![Runtime](https://img.shields.io/badge/Automation-Timely-111111)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![Result](https://img.shields.io/badge/Result-Finalist%207%20of%2012-C5962A)

</div>

## Overview

Campus Mate connects a fragmented process—finding notices, reading eligibility and deadlines, prioritizing opportunities, and copying dates into a calendar—into one controlled workflow:

```text
collect → parse with evidence → rank → Notion → Slack → user Accept → Calendar
```

The repository combines an official Claude Code `.claude/` harness with an installable Python execution layer. The six functional agents express domain responsibilities; three operational agents package them into Timely schedules.

## Agent architecture

### Functional agents

- `profile-manager`
- `source-collector`
- `multipass-parser`
- `fit-priority`
- `notion-dashboard`
- `schedule-notification`

### Operational agents

- `daily-collector` — 08:00
- `slack-briefing` — 09:00
- `accept-sync` — hourly

The main entry point is `/campus-mate-orchestrator`. Eighteen modular skills define parsing, ranking, synchronization, and QA contracts. Each Markdown component maps to concrete Python modules, outputs, validation gates, and recovery rules.

## Key safeguards

- No fabricated deadlines or eligibility conditions
- Field-level evidence and confidence
- Non-destructive Notion upsert
- User-controlled states preserved
- Slack is notification-only
- Calendar events require Notion `Accept`
- Per-request calendar result handling and idempotency
- Environment-backed secrets and credential guards

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[ocr,vision,dev]'
python -m playwright install chromium
cp .env.example .env
```

Run Claude Code in the repository and request:

```text
Start Campus Mate onboarding
Run the Campus Mate fixture demo
Collect today's notices and sync them to Notion
Generate a Slack briefing dry run
Apply accepted opportunities to the calendar
```

Direct skill invocation:

```text
/campus-mate-orchestrator demo
/campus-mate-onboarding
/campus-mate-demo fixture
```

Deterministic local demo:

```bash
cp examples/profile.example.json data/user_profile.json
CAMPUS_MATE_STORAGE_BACKEND=json \
  campus-mate demo --fixture examples/fixtures/linkareer_detail.html
```

## Verification

```bash
python -m pytest -q
python scripts/validate_harness.py
python scripts/scan_secrets.py .
python -m compileall -q src scripts
```

## Documentation

- [`CLAUDE.md`](./CLAUDE.md) — project invariants
- [`spec.md`](./spec.md) — requirements and acceptance criteria
- [`workflow.md`](./workflow.md) — phases, handoffs, and recovery
- [`role-table.md`](./role-table.md) — agent/skill/code mapping
- [`docs/timely-deployment.md`](./docs/timely-deployment.md) — scheduled runtime setup
- [`docs/data-contracts.md`](./docs/data-contracts.md) — cross-phase schemas

## Scope

The packaged production source adapter is Linkareer. OCR and poster vision are optional. Notion and Slack are handled by the Python package; Google Calendar creation uses a Timely/Composio request/result bridge.

## Project materials

| Material | Link | Contents |
|---|---|---|
| Presentation | [2026 Campus Mate presentation](./materials/2026-campus-mate-presentation.pptx) | Problem, system architecture, six functional roles, and automation flow |
| Script | [Seven-minute presentation script](./materials/2026-campus-mate-7min-script.docx) | Timely demo and Notion, Slack, and Calendar integration narrative |

## Project

- Harness Engineering: AI Agent & Skill Hackathon
- Finalist, 7 of 12 teams
- Team project · Architecture & Development Lead

No open-source license is granted in this package pending team agreement.
