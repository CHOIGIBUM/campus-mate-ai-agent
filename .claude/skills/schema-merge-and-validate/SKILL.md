---
name: schema-merge-and-validate
description: >-
  HTML·OCR·Vision 후보를 필드별 우선순위로 병합하고 근거·신뢰도·충돌·NeedsReview 상태를 결정한다.
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

# 스키마 병합·검증

[필드 출처 우선순위](references/field-precedence.md)를 적용합니다.

## 절차

1. 후보를 필드 단위로 비교합니다.
2. 구조화 데이터와 화면 HTML을 우선합니다.
3. 선택·비선택 근거를 모두 저장합니다.
4. 날짜·자격·혜택 충돌을 검출합니다.
5. `Opportunity` 모델로 정규화합니다.
6. `parse_confidence`, `parse_warnings`, 검토 상태를 계산합니다.

## 최소 저장 조건

- `title`
- `source`
- `source_url`
- `opportunity_id`

## 상태

- 최소 필드 누락: `FAIL`
- 핵심 필드 충돌: `NEEDS_REVIEW`
- 그 외: `PASS`

마감일이 없거나 충돌한 항목은 Calendar 요청 대상에서 제외합니다.

## 검증

```bash
python -m pytest tests/test_multipass.py -q
```
