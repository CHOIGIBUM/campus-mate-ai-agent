---
name: schema-merge-and-validate
description: >-
  HTML·OCR·Vision ParseCandidate를 필드별 우선순위와 신뢰도에 따라 병합하고 충돌, 경고, 전체 파싱 신뢰도, NeedsReview 여부를 결정한다.
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

# 스키마 병합과 검증

## 병합 규칙

먼저 [필드 출처 우선순위](references/field-precedence.md)를 읽습니다.

1. 문서 전체가 아니라 필드별로 병합합니다.
2. 구조화 데이터와 HTML 근거를 우선합니다.
3. 선택되지 않은 근거도 모두 보존합니다.
4. 서로 양립할 수 없는 날짜와 텍스트를 감지합니다.
5. 결과를 `Opportunity` 모델로 정규화합니다.
6. 경고와 검토 상태를 설정합니다.

## 필수 통과 필드

- title
- source
- source_url
- opportunity_id

## 일정 생성 통과 조건

마감일이 충돌하거나 누락된 공고는 자동 마감 일정을 만들 수 없습니다.

## 검증

```bash
python -m pytest tests/test_multipass.py -q
```
