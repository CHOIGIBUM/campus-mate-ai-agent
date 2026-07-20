# Data Contracts

Canonical validation is implemented with Pydantic in `src/campus_mate/models.py`.

## User profile

```json
{
  "name": "홍길동",
  "school": "강원대학교",
  "grade": "3학년",
  "major": "AI융합학과",
  "interests": ["AI", "디지털 헬스케어"],
  "activity_types": ["공모전", "해커톤"],
  "career_goal": "AI 엔지니어",
  "keywords": ["Python", "LLM", "의료 AI"],
  "preferred_regions": ["온라인", "강원"],
  "available_times": ["평일 저녁", "주말"]
}
```

Required: `school`, `grade`, `major`, non-empty `interests`.

## Opportunity

```json
{
  "opportunity_id": "stable hash",
  "source": "linkareer",
  "source_url": "https://...",
  "title": "공모전 제목",
  "organization": "주최기관",
  "opportunity_type": "공모전",
  "summary": "핵심 내용",
  "eligibility": "대학생",
  "submission": "기획서 PDF",
  "benefits": "상금 및 교육",
  "deadline": "2026-08-31",
  "event_date": "2026-09-15",
  "poster_url": "https://...",
  "parse_confidence": 0.91,
  "parse_evidence": {
    "deadline": [
      {"source": "next_data", "confidence": 0.98, "raw_excerpt": "..."}
    ]
  },
  "parse_warnings": [],
  "fit_score": 84,
  "priority": "중요",
  "recommendation_reasons": ["AI 관심 분야와 일치"],
  "status": "Recommended",
  "conflict_status": "미확인",
  "calendar_event_ids": {}
}
```

## Parse evidence precedence

Default order:

1. explicit structured source (`jsonld`, `next_data`)
2. visible HTML
3. OCR
4. vision
5. fallback/manual

A lower-priority source may win only if it has clearly stronger evidence and the conflict is documented. Unresolved core-field conflict sets a warning and may require review.

## Calendar request

```json
{
  "request_id": "opp-id:deadline",
  "opportunity_id": "opp-id",
  "notion_page_id": "page-id",
  "kind": "deadline",
  "summary": "[마감] 공모전 제목",
  "start_datetime": "2026-08-31T23:00:00+09:00",
  "duration_minutes": 60,
  "timezone": "Asia/Seoul",
  "description": "원문 URL 및 준비사항",
  "calendar_id": "primary",
  "idempotency_key": "stable-key"
}
```

## Calendar result

```json
{
  "request_id": "opp-id:deadline",
  "success": true,
  "event_id": "google-event-id",
  "error": "",
  "raw": {}
}
```

The result file must preserve `request_id`; array order is not sufficient for matching.

## Handoff envelope

See `workflow.md`. Handoffs are phase-control records, not replacements for domain models.
