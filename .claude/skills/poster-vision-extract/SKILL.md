---
name: poster-vision-extract
description: >-
  포스터 이미지에서 HTML·OCR 이후에도 누락된 공고 필드를 추출하고 Vision 근거를 반환한다. Vision 결과만으로 모호한 핵심 필드를 확정하지 않는다.
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

## 실행 전 조건

- 포스터 이미지 URL 또는 로컬 경로가 존재해야 합니다.
- `CAMPUS_MATE_VISION_API_KEY`와 모델이 설정되어 있어야 합니다.
- HTML·OCR 이후에도 중요한 필드가 누락됐거나 `--all-passes`가 요청돼야 합니다.

## 요청할 필드

마감일, 참가 자격, 혜택, 행사일, 주최기관처럼 누락됐고 중요도가 높은 필드만 요청합니다.

## 출력 조건

- JSON으로 변환 가능한 값
- 근거가 되는 이미지 설명 또는 발췌
- 신뢰도
- 내부 추론 과정은 출력하지 않음
- 이미지에 보이지 않는 정보는 추론하지 않음

## 실패 처리

모델 사용 불가, 이미지 다운로드 실패, 잘못된 JSON 응답이 발생하면 경고를 남기고 다른 pass 결과로 계속 진행합니다.

## 구현

`src/campus_mate/parsing/vision.py`
