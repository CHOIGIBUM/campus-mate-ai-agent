# spec.md — rendered-page-ocr Skill

## 목표
웹페이지를 렌더링/PDF 변환 후 OCR로 텍스트를 추출하여, HTML 파싱으로 누락된 정보(특히 카드형 UI, 동적 콘텐츠)를 보완한다.

## 맥락
**대상:** 공고 URL의 렌더링된 페이지  
**사용 목적:** Multi-pass Parser Agent의 2차 파싱 단계

## 범위

**포함:**
- 웹페이지 PDF/이미지 렌더링 (Playwright, Selenium 또는 클라우드 서비스)
- OCR (Tesseract, EasyOCR)
- 마감일, 금액, 연락처 등 숫자/날짜 추출
- 각 필드별 confidence 기록

**제외:**
- 웹페이지 상호작용 (클릭, 스크롤)
- 로그인 자동화

## 입력 예시

```json
{
  "opportunity_url": "https://example.com/opp",
  "timeout": 10
}
```

## 출력 예시

```json
{
  "parse_method": "rendered_ocr",
  "extracted_fields": {
    "deadline": {
      "value": "2026-07-15T23:59:00+09:00",
      "evidence": "OCR extracted text: 마감: 7월 15일 23:59",
      "confidence": 75
    }
  },
  "status": "success"
}
```

## 성공 기준

- [ ] 렌더링 완료 후 OCR로 텍스트 추출된다
- [ ] 날짜/시간이 정확히 인식된다
- [ ] confidence가 HTML 결과와 비교 가능하다
- [ ] 타임아웃(10초) 초과 시 status = "timeout" 기록된다
