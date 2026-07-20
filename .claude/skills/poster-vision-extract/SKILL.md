---
name: poster-vision-extract
description: >-
  포스터 이미지에서 HTML·OCR 이후 남은 핵심 필드를 추출하고 근거·신뢰도를 반환한다.
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

# 포스터 Vision 추출

## 실행 조건

- 포스터 이미지 URL 또는 로컬 경로 존재
- Vision API key와 모델 설정 존재
- 핵심 필드 누락 또는 `--all-passes` 지정

## 대상 필드

- 마감일
- 행사일
- 참가 자격
- 혜택
- 주최기관

## 규칙

- 필요한 필드만 요청합니다.
- JSON 형식으로 결과를 반환합니다.
- 이미지에 보이지 않는 정보를 추론하지 않습니다.
- 각 값에 근거 설명과 신뢰도를 포함합니다.
- 실행 불가 시 `SKIPPED`, 응답 오류 시 `FAIL`을 반환합니다.

## 출력

- `ParseCandidate`
- 필드별 근거·신뢰도
- 상태와 오류

## 구현

`src/campus_mate/parsing/vision.py`
