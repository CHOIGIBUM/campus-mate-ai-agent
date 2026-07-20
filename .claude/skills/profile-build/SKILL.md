---
name: profile-build
description: >-
  Campus Mate 사용자 온보딩과 프로필 수정을 수행한다. 기존 프로필을 읽고 필수 누락값만 질문한 뒤 UserProfile 계약으로 정규화·검증·저장하고 추천에 사용할 제한적 검색어를 생성한다.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - Edit
---

# 프로필 생성·수정

## 입력

대화에서 수집한 값 또는 JSON 객체를 사용합니다.

필수 필드:

- `school`
- `grade`
- `major`
- 값이 1개 이상인 `interests`

선택 필드:

- 활동 유형
- 희망 직무
- 사용자가 직접 입력한 키워드
- 선호 지역
- 가능한 시간대

## 대화형 진행 절차

1. `data/user_profile.json`이 있으면 현재 프로필을 읽습니다.
2. 질문 전에 현재 값을 짧게 요약합니다.
3. 누락됐거나 사용자가 바꾸려는 필드만 질문합니다.
4. 전화번호, 주민등록번호 등 추천과 무관한 민감정보는 수집하지 않습니다.
5. 쉼표로 입력된 값을 배열로 변환합니다.
6. 앞뒤 공백을 제거하고 대소문자를 무시해 중복을 정리합니다.
7. 사용자의 표현을 유지하며 공식 학과명 등을 임의로 만들어내지 않습니다.
8. `UserProfile`로 검증합니다.
9. 저장 후 핵심 내용을 간단히 보여주고 확인받습니다.

## 명령

```bash
campus-mate profile init
campus-mate profile import --file <profile.json>
campus-mate profile show
```

## 검색어 생성

전공, 관심 분야, 희망 직무, 사용자가 직접 입력한 키워드에서 검색어를 만듭니다.

- 원래 표현을 유지합니다.
- 일반적인 구분자를 기준으로 나눕니다.
- 의미가 명확히 가까운 동의어만 추가합니다.
- 의미가 지나치게 넓어지지 않도록 확장 수를 제한합니다.
- 민감한 특성을 추론하지 않습니다.

검색어만 확인하는 명령:

```bash
campus-mate-skill interest-keyword-expand --profile <profile.json>
```

## 출력

- `data/user_profile.json`
- 프로필 요약
- 검색어 목록
- 변경된 필드 목록

실패할 경우 누락됐거나 형식이 잘못된 필드를 정확히 알려줍니다. 조용히 기본 프로필을 만들지 않습니다.

## 구현

- `src/campus_mate/services/onboarding.py`
- `src/campus_mate/services/keywords.py`
- `src/campus_mate/models.py::UserProfile`
- `tests/test_onboarding.py`
