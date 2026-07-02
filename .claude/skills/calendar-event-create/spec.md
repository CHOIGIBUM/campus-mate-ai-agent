# spec.md — calendar-event-create Skill

## 목표
Google Calendar에 마감일, 행사일, 준비 일정을 자동으로 생성하고, 생성된 이벤트 ID를 기록한다.

## 맥락
**대상:** Google Calendar API Token, 공고 정보  
**사용 목적:** Calendar Scheduler Agent에서 호출하여 일정 생성

## 범위

**포함:**
- Google Calendar Events.insert API 호출
- 마감일 일정 생성 (23:59)
- 행사일 일정 생성 (시작~종료 시간)
- 준비 일정 생성 (D-5~D-1)
- 생성된 event_id 반환

**제외:**
- 충돌 검사 (calendar-freebusy-check가 담당)

## 입력 예시

```json
{
  "calendar_token": "...",
  "events": [
    {
      "title": "의료 데이터 AI 해커톤 - 마감",
      "start": "2026-07-15T23:59:00+09:00",
      "end": "2026-07-16T00:00:00+09:00",
      "description": "..."
    }
  ]
}
```

## 출력 예시

```json
{
  "created_events": [
    {
      "event_type": "deadline",
      "google_event_id": "abc123",
      "status": "created"
    }
  ]
}
```

## 성공 기준

- [ ] 모든 일정이 Google Calendar에 생성된다
- [ ] event_id가 정확히 반환된다
- [ ] 시간이 올바른 시간대로 저장된다
