# spec.md — schema-merge-and-validate Skill

## 목표
3단계 파싱 결과(HTML, OCR, Vision)를 표준 JSON 스키마로 병합하고, 필드 충돌을 감지하며, 신뢰도에 따라 최종 값을 선택한다.

## 맥락
**대상:** 3단계 파싱 결과 (html_result, ocr_result, vision_result)  
**사용 목적:** Multi-pass Parser Agent의 최종 병합 단계

## 범위

**포함:**
- 3단계 결과 통합 (필드별 비교)
- confidence 기반 우선순위 (HTML > OCR > Vision)
- 동일 필드 값 차이 감지 → "conflict" 플래그
- 필드별 evidence 및 source_method 기록
- "확인 필요" 정책 (불명확하면 추측 금지)

**제외:**
- 추천이나 우선순위 판단

## 입력 예시

```json
{
  "html_result": {...},
  "ocr_result": {...},
  "vision_result": {...}
}
```

## 출력 예시

```json
{
  "opportunity_id": "opp_20260702_001",
  "basic_info": {
    "title": "의료 데이터 AI 해커톤",
    "deadline": "2026-07-15T23:59:00+09:00"
  },
  "extraction_metadata": {
    "deadline": {
      "source_method": "ocr",
      "evidence": "마감: 2026-07-15 23:59",
      "confidence": 80,
      "conflict": {
        "html": "2026-07-20",
        "vision": "2026-07-15",
        "status": "needs_review"
      }
    }
  }
}
```

## 성공 기준

- [ ] 3단계 결과가 모두 비교되고, 최종 값이 선택된다
- [ ] 다른 값이 추출되면 conflict 표시되고 needs_review로 남는다
- [ ] 모든 필드에 evidence와 confidence가 포함된다
