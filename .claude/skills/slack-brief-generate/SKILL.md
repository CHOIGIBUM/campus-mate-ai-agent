---
name: slack-brief-generate
description: >-
  Recommended 공고를 Slack Block Kit 브리핑으로 정리하고 dry-run 또는 실제 전송을 수행한다. 승인 안내는 Notion으로 연결한다.
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
  - Agent
  - Skill
---

# Slack Brief Generate

Read [brief-format.md](references/brief-format.md).

## Dry run

```bash
campus-mate brief --dry-run --output artifacts/slack-briefing.json
```

## Delivery

```bash
campus-mate brief
```

## Rules

- Recommended only
- urgent/high score first
- show deadline, score, reason, conflict
- approval is in Notion
- no token/profile private fields in payload/log

## Verify

```bash
python -m pytest tests/test_slack.py -q
```
