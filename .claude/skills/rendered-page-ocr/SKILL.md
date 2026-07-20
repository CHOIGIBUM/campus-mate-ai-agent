---
name: rendered-page-ocr
description: >-
  HTML에서 빠진 텍스트를 보완하기 위해 Playwright 렌더링 화면 또는 포스터 이미지를 OCR하고, OCR 근거와 낮음·중간 수준의 신뢰도 후보를 반환한다.
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

## 사용하는 경우

- 결정적인 HTML 출처에 날짜·참가 자격·제출물 정보가 없을 때
- 중요한 내용이 이미지 또는 렌더링된 카드 안에만 있을 때

## 준비 사항

- 선택 의존성 `ocr`
- 페이지 렌더링이 필요하면 Playwright Chromium
- Tesseract `kor+eng` 언어팩

## 규칙

- OCR 결과는 보조 근거이며 자동으로 정답으로 간주하지 않습니다.
- 인식한 원문 발췌를 그대로 보존합니다.
- 모호한 숫자는 경고로 남깁니다.
- 실행할 수 없으면 결과를 만들지 말고 `skipped`로 기록합니다.

## 구현

`src/campus_mate/parsing/ocr.py`

## 검증

```bash
python -m pytest tests/test_ocr_parser.py -q
```
