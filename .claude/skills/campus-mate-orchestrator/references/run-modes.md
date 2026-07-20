# Orchestrator 실행 모드

| 모드 | 목적 | 기본 외부 변경 |
|---|---|---|
| `status` | 설정, 계약 문서, 최근 산출물 확인 | 없음 |
| `onboard` | `profile-manager`를 통한 프로필 생성·수정 | 로컬 프로필 쓰기 |
| `demo` | 기본은 fixture, 명시적으로 허용된 경우만 live 실행 | 기본 JSON 저장 |
| `daily` | 공고 수집, 파싱, 추천, upsert | 설정 시 Notion |
| `brief` | 추천 브리핑 생성 또는 전송 | 대화형 실행은 dry-run |
| `accept-sync` | 승인된 공고의 Calendar 계획·결과 반영 | Calendar와 Notion |
| `partial:<phase>` | 특정 단계와 필요한 후속 단계 재실행 | 단계에 따라 다름 |

Timely는 `daily`, `brief`, `accept-sync`를 일정에 따라 실행합니다. 이 자동화 이름을 별도 Agent로 정의할 필요는 없습니다.
