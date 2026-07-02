# spec.md — calendar-freebusy-check Skill

## 목표
Google Calendar에서 특정 시간 범위의 일정을 조회하여 기존 일정과의 충돌 여부를 확인한다.

## 맥락
**대상:** Google Calendar API Token, 시간 범위  
**사용 목적:** Calendar Scheduler Agent에서 호출하여 충돌 검사

## 범위

**포함:**
- Google Calendar freebusy 쿼리
- 1시간 이상 겹치면 conflict 판정
- 충돌하는 이벤트 정보 반환

**제외:**
- 일정 생성 (calendar-event-create가 담당)

## 입력 예시

```json
{
  "calendar_token": "...",
  "time_min": "2026-07-22T10:00:00+09:00",
  "time_max": "2026-07-22T18:00:00+09:00"
}
```

## 출력 예시

```json
{
  "conflict_status": "no_conflict",
  "busy_events": []
}
```

## 성공 기준

- [ ] 기존 일정과의 겹침이 정확히 감지된다
