# spec.md — poster-vision-extract Skill

## 목표
공고 포스터 이미지를 다운로드하여 Vision API로 분석하고, 주최, 일정, 시상, 참가 대상, 연락처 정보를 추출한다.

## 맥락
**대상:** 공고 웹페이지에서 찾은 포스터 이미지  
**사용 목적:** Multi-pass Parser Agent의 3차 파싱 단계

## 범위

**포함:**
- 웹페이지에서 이미지 링크 추출
- 포스터 이미지 다운로드
- Vision API (Google Cloud Vision, Claude Vision) 분석
- 한글/영문 텍스트 추출
- QR 코드 감지

**제외:**
- 이미지 직접 가공/필터링

## 입력 예시

```json
{
  "image_urls": ["https://example.com/poster.png"],
  "vision_api": "claude_vision"
}
```

## 출력 예시

```json
{
  "parse_method": "vision",
  "extracted_fields": {
    "organizer": {
      "value": "데이콘",
      "evidence": "Image contains text: 주최: 데이콘",
      "confidence": 85
    },
    "deadline": {
      "value": "2026-07-15T23:59:00+09:00",
      "evidence": "마감: 7/15 23:59",
      "confidence": 80
    }
  },
  "status": "success"
}
```

## 성공 기준

- [ ] 포스터 이미지에서 주요 텍스트가 추출된다
- [ ] 날짜, 시상, 연락처가 정확히 인식된다
- [ ] 이미지 없음 시 status = "no_image" 기록된다
