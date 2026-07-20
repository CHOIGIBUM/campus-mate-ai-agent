# Orchestrator 실행 모드

| 모드 | 실행 범위 | 기본 외부 변경 |
|---|---|---|
| `status` | 설정·계약·산출물 확인 | 없음 |
| `onboard` | 프로필 생성·수정 | 로컬 프로필 |
| `demo` | fixture 기반 전체 흐름 | JSON 저장소 |
| `daily` | 수집·파싱·추천·Notion | 설정 시 Notion |
| `brief` | Slack 브리핑 | 대화형 실행은 dry-run |
| `accept-sync` | Accept 공고 Calendar 동기화 | Calendar·Notion |
| `partial:<phase>` | 지정 단계와 후속 단계 | 단계별 |

Timely는 `daily`, `brief`, `accept-sync`를 일정에 따라 호출합니다.
