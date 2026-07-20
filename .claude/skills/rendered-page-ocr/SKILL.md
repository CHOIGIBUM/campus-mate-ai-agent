---
name: rendered-page-ocr
description: >-
  HTML에서 확인되지 않은 필드를 렌더링 화면 또는 포스터 OCR로 추출한다.
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

# 렌더링 페이지 OCR

## 실행 조건

- 핵심 필드가 HTML 결과에 없음
- 정보가 렌더링 카드 또는 이미지에 존재
- OCR 의존성과 `kor+eng` 언어팩 사용 가능

## 규칙

- OCR 결과를 보조 근거로 사용합니다.
- 인식 원문을 그대로 저장합니다.
- 숫자·날짜 모호성은 `warnings`에 기록합니다.
- 실행 조건을 만족하지 않으면 상태를 `SKIPPED`로 반환합니다.

## 출력

- `ParseCandidate`
- OCR 원문
- 필드별 신뢰도
- warnings
- 상태: `PASS`, `SKIPPED`, `FAIL`

## 구현·검증

- `src/campus_mate/parsing/ocr.py`
- `python -m pytest tests/test_ocr_parser.py -q`
