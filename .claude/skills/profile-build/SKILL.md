---
name: profile-build
description: >-
  사용자 프로필을 수집·정규화·검증하고 추천용 검색어를 생성한다.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# 프로필 생성·수정

## 입력 계약

필수:

- `school`
- `grade`
- `major`
- `interests` 1개 이상

선택:

- `activity_types`
- `career_goal`
- `keywords`
- `preferred_regions`
- `available_times`

## 절차

1. 기존 `data/user_profile.json`을 읽습니다.
2. 누락 또는 변경 필드만 수집합니다.
3. 목록형 입력의 공백과 중복을 정리합니다.
4. 사용자가 입력한 표현을 유지합니다.
5. `UserProfile`로 검증합니다.
6. 프로필과 검색어를 저장합니다.

## 검색어 규칙

- 전공, 관심 분야, 희망 직무, 직접 입력 키워드를 사용합니다.
- 명확한 동의어만 제한적으로 추가합니다.
- 민감한 특성을 추론하지 않습니다.
- 범위를 과도하게 넓히지 않습니다.

## 명령

```bash
campus-mate profile init
campus-mate profile import --file <profile.json>
campus-mate profile show
```

## 출력

- `data/user_profile.json`
- 검색어 목록
- 변경 필드 목록
- 검증 오류 목록

## 구현

- `src/campus_mate/services/onboarding.py`
- `src/campus_mate/services/keywords.py`
- `src/campus_mate/models.py::UserProfile`
- `tests/test_onboarding.py`
