# Calendar 커넥터 계약

| 종류 | 제목 형식 | 기본 시간 |
|---|---|---|
| `deadline` | `[마감] 공고명` | 23:00 KST |
| `preparation` | `[D-3 준비] 공고명` | 09:00 KST |
| `event` | `[행사] 공고명` | 09:00 KST |

모든 connector 결과는 원래 `request_id`를 유지합니다. timeout과 결과 누락은 실패로 처리합니다. 생성된 event ID는 공고 레코드에 저장합니다.
