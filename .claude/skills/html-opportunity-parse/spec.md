# spec.md — html-opportunity-parse Skill

## 목표
웹페이지의 HTML 본문을 파싱하여 공고 제목, 마감일, 기간, 주최, 참가 자격, 제출물 정보를 추출한다.

## 맥락
**대상:** 공고 URL의 HTML 콘텐츠  
**사용 목적:** Multi-pass Parser Agent의 1차 파싱 단계

## 범위

**포함:**
- HTML 다운로드 및 인코딩 자동 감지
- CSS selector 기반 텍스트 추출
- 정규식으로 날짜, 시간, 금액 형식 추출
- 추출 근거(evidence) 기록

**제외:**
- JavaScript 렌더링 (rendered-page-ocr가 담당)
- 이미지 처리

## 입력 예시

```json
{
  "opportunity_url": "https://dacon.io/competitions/xxx",
  "site_name": "Dacon"
}
```

## 출력 예시

```json
{
  "parse_method": "html",
  "extracted_fields": {
    "title": {
      "value": "의료 데이터 AI 해커톤",
      "evidence": "<h1>의료 데이터 AI 해커톤</h1>",
      "confidence": 95
    },
    "submission_deadline": {
      "value": "2026-07-15T23:59:00+09:00",
      "evidence": "마감: 2026-07-15 23:59",
      "confidence": 90
    }
  },
  "status": "success"
}
```

## 성공 기준

- [ ] 제목이 추출된다
- [ ] 마감일이 ISO 8601 형식으로 변환된다
- [ ] 각 필드에 evidence(원문 스니펫)가 포함된다
- [ ] HTML 파싱 실패 시 status = "failed" 기록된다
