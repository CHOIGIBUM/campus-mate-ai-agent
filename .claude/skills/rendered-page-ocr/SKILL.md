---
name: rendered-page-ocr
description: >-
  HTML에서 빠진 텍스트를 보완하기 위해 Playwright 렌더링 또는 포스터 이미지를 OCR하고, OCR evidence와 낮은/중간 confidence 후보를 반환한다.
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

# Rendered Page OCR

## Use when

- date/eligibility/submission fields are absent from deterministic HTML sources
- important content is embedded in an image or rendered card

## Prerequisites

- optional `ocr` dependencies
- Playwright Chromium when page rendering is needed
- Tesseract `kor+eng` language packs

## Rules

- OCR is supporting evidence, not automatic ground truth.
- Preserve the exact excerpt.
- Ambiguous digits remain warnings.
- If unavailable, record `skipped` rather than fabricating output.

## Implementation

`src/campus_mate/parsing/ocr.py`

## Verify

```bash
python -m pytest tests/test_ocr_parser.py -q
```
