# Run Mode Decision Table

| User phrase | Mode | Default write policy |
|---|---|---|
| 온보딩 시작 / 프로필 설정 | onboard | local profile only |
| 시연 시작 / demo | demo | JSON backend unless “실제 연동” explicit |
| 오늘 공고 수집 / 일일 파이프라인 | daily | confirm Notion write in interactive sessions |
| 브리핑 만들어 | brief | dry-run |
| 브리핑 보내 | brief | Slack write after config check |
| 승인 반영 | accept-sync | Calendar write requires result connector |
| 상태 확인 / 뭐가 준비됐어 | status | read-only |
| 파싱만 다시 | partial:parse | no unrelated phases |
