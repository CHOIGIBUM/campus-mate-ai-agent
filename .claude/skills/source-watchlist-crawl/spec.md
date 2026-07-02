# spec.md — source-watchlist-crawl Skill

## 목표
등록된 공고 사이트를 순회하여 HTML 링크를 추출하고, 중복 제거 후 신규 URL 목록을 반환한다.

## 맥락
**대상:** Source Watchlist의 7개 사이트  
**사용 목적:** Source Collector Agent가 매일 호출하여 신규 공고 URL 수집

## 범위

**포함:**
- 각 사이트별 크롤링 로직 (requests + BeautifulSoup 또는 유사)
- 공고 링크 패턴 추출 (CSS selector, XPath 등)
- 기존 저장 URL과 비교하여 신규 URL만 필터링
- 각 사이트별 상태(success/failure/skipped) 기록
- 에러 메시지 기록

**제외:**
- 상세 공고 파싱
- JavaScript 렌더링 (필요시 다른 Skill에서 담당)

## 입력 예시

```json
{
  "sites": [
    {
      "site_name": "링커리어",
      "source_url": "https://www.linkareer.com",
      "crawl_selector": "a.opportunity-card"
    }
  ],
  "existing_urls": ["https://linkareer.com/opp1", "https://linkareer.com/opp2"]
}
```

## 출력 예시

```json
{
  "crawl_date": "2026-07-02",
  "site_results": [
    {
      "site_name": "링커리어",
      "status": "success",
      "all_urls_found": 15,
      "new_urls": ["https://linkareer.com/opp_new1", "https://linkareer.com/opp_new2"],
      "new_count": 2
    }
  ],
  "total_new_urls": 12,
  "new_urls_all": [...]
}
```

## 성공 기준

- [ ] 각 사이트에서 공고 링크가 정확히 추출된다
- [ ] 중복이 제거되고 신규 URL만 반환된다
- [ ] 각 사이트별 성공/실패 상태가 기록된다
- [ ] 타임아웃(30초)을 초과하면 실패로 처리된다
