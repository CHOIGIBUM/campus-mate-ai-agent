---
name: slack-brief-generate
description: >-
  Recommended 공고를 Slack Block Kit 브리핑으로 정리하고 dry-run 또는 실제 전송을 수행한다. 참가 승인 안내는 Notion으로 연결한다.
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

# Slack 브리핑 생성

먼저 [브리핑 형식](references/brief-format.md)을 읽습니다.

## Dry-run

```bash
campus-mate brief --dry-run --output artifacts/slack-briefing.json
```

## 실제 전송

```bash
campus-mate brief
```

## 규칙

- `Recommended` 상태만 포함합니다.
- 긴급도와 높은 점수를 우선하고, 같은 조건에서는 마감일을 고려합니다.
- 마감일, 적합도, 추천 이유, 충돌 상태를 보여줍니다.
- 참가 승인은 Notion에서 처리합니다.
- payload와 로그에 token 또는 비공개 프로필 필드를 넣지 않습니다.

## 검증

```bash
python -m pytest tests/test_slack.py -q
```
