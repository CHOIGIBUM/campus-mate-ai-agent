---
name: profile-build
description: 사용자의 온보딩 입력값(이름, 학교, 학과, 학년, 관심 분야, 희망 직무, 선호 활동, 지역, 가능 시간)을 JSON 구조로 정규화하고 저장하는 스킬
---

# Profile Build Skill

사용자 프로필 정보를 구조화하고 JSON으로 저장합니다.

## 사용 시기

Profile Agent가 사용자 온보딩 정보를 입력받은 직후

## 입력

- 이름, 학교, 학과, 학년
- 관심 분야(배열), 희망 직무(배열)
- 선호 활동 유형, 활동 가능 지역
- 주간 투자 가능 시간
- Kakao 보고 시간

## 출력

- `user_profile_{user_id}.json` 파일
- basic_info, interests, career_goal, preferences, availability, metadata 섹션 포함
- 타임스탬프, 버전 정보 기록

## 주의사항

- 입력되지 않은 필드는 기록하지 않습니다
- 학년, 지역 등은 표준 분류를 사용합니다
- 같은 사용자는 같은 user_id를 유지합니다
