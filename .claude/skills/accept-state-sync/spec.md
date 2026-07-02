# spec.md — accept-state-sync Skill

## 목표
Notion에서 감지한 Accept 상태 변경을 Timely 내부 상태로 동기화하고, Calendar Scheduler에 신호를 전달한다.

## 맥락
**대상:** Notion 상태 변경 감지  
**사용 목적:** Notion Dashboard Agent에서 호출하여 상태 동기화

## 범위

**포함:**
- Accept 상태 변경 기록
- 내부 workflow 상태 업데이트 (calendar_status = "pending_creation")
- Calendar Scheduler Agent에 신호 반환

**제외:**
- 실제 일정 생성 (calendar-event-create가 담당)

## 입력 예시

```json
{
  "opportunity_id": "opp_...",
  "status_old": "Recommended",
  "status_new": "Accept"
}
```

## 출력 예시

```json
{
  "sync_status": "success",
  "workflow_status": "pending_calendar_creation",
  "trigger_calendar_scheduler": true
}
```

## 성공 기준

- [ ] Accept 상태 변경이 정확히 기록된다
- [ ] Calendar Scheduler에 신호가 전달된다
