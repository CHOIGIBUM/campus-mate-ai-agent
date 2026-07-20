---
name: slack-brief-generate
description: >-
  Recommended 공고를 Slack Block Kit payload로 생성하고 dry-run 또는 실제 전송을 수행한다.
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

# Slack 브리핑

[브리핑 형식](references/brief-format.md)을 적용합니다.

## 입력

- `Recommended` 공고
- Notion 링크 또는 원문 링크
- 충돌 상태

## 절차

1. 우선순위, 점수, 마감일로 정렬합니다.
2. 공고별 Block Kit 블록을 생성합니다.
3. dry-run에서는 payload를 파일로 저장합니다.
4. 실제 전송에서는 설정된 채널로 1회 전송합니다.

## 명령

```bash
campus-mate brief --dry-run --output artifacts/slack-briefing.json
campus-mate brief
```

## 제약

- `Recommended` 상태만 포함합니다.
- token과 비공개 프로필 필드를 payload·로그에 넣지 않습니다.
- Slack 입력을 참가 승인으로 처리하지 않습니다.

## 검증

```bash
python -m pytest tests/test_slack.py -q
```
