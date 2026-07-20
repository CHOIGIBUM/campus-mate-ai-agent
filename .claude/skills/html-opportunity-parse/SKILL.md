---
name: html-opportunity-parse
description: >-
  공고 상세 페이지의 JSON-LD, Next.js 상태, 화면에 표시된 HTML에서 제목·기관·날짜·자격·제출물·혜택·포스터를 추출하고 필드별 근거를 생성한다.
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

# HTML 공고 파싱

## 근거 우선순위

1. JSON-LD
2. Next.js 상태 데이터 (`__NEXT_DATA__` 또는 동등한 구조)
3. 화면에 표시된 HTML 라벨과 텍스트 영역

## 출력

`values`, `evidence`, 경고를 포함한 `ParseCandidate`를 반환합니다.

## 규칙

- 각 필드에 사용한 원문 발췌를 보존합니다.
- 날짜는 보수적으로 해석합니다.
- 누락된 참가 자격이나 혜택을 추론하지 않습니다.
- 형식은 정규화할 수 있지만 원문의 의미를 바꾸지 않습니다.

## 구현

- `src/campus_mate/parsing/html.py`
- `tests/test_html_parser.py`

## 검증

```bash
python -m pytest tests/test_html_parser.py -q
```
