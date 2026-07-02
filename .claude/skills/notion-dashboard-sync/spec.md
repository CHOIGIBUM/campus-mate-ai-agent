# spec.md — notion-dashboard-sync Skill

## 목표
Notion 데이터베이스에 공고 카드를 생성/갱신하고, 사용자의 상태 변경(Accept/Hold/Reject)을 감지하여 Timely 내부 상태와 동기화한다.

## 맥락
**대상:** Notion Integration Token, 공고 정보  
**사용 목적:** Notion Dashboard Agent에서 호출하여 현황판 관리

## 범위

**포함:**
- Notion API 호출 (create, update, read)
- 새 카드 생성 (15개 Property 설정)
- 기존 카드 갱신
- Status 필드 모니터링 (1분 주기)
- Accept 감지 시 신호 반환

**제외:**
- 데이터베이스 초기 스키마 설계

## 입력 예시

```json
{
  "notion_token": "secret_...",
  "database_id": "123...",
  "opportunity": {...}
}
```

## 출력 예시

```json
{
  "action": "created",
  "notion_page_id": "abc123",
  "status": "New"
}
```

## 성공 기준

- [ ] 카드가 Notion에 생성된다
- [ ] Accept 상태 변경이 감지된다
- [ ] 중복 생성 방지
