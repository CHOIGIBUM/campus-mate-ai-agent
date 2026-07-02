# spec.md — kakao-brief-generate Skill

## 목표
신규 추천 공고, 긴급 마감, 일정 충돌, 확인 필요 항목을 수집하여 짧은 한글 메시지로 포맷팅한다.

## 맥락
**대상:** 오늘의 공고 현황 데이터  
**사용 목적:** Kakao Report Agent에서 호출하여 보고 메시지 생성

## 범위

**포함:**
- 신규 추천 TOP 3–5개 선별
- 긴급 마감(D-7 이내) 추출
- 충돌 공고 안내
- 확인 필요 공고 리스트
- 마크다운 + 이모지 포맷팅
- Notion 링크 추가

**제외:**
- 실제 Kakao API 발송

## 입력 예시

```json
{
  "user_name": "최기범",
  "new_recommendations": [...],
  "urgent_deadlines": [...],
  "conflicts": [...],
  "needs_review": [...],
  "notion_url": "https://..."
}
```

## 출력 예시

```markdown
# [Campus Career AI] 최기범님 기준 오늘의 공모전 브리핑

## 🔥 긴급 마감
- 의료 데이터 AI 해커톤 (D-5)

## ⭐ 신규 추천
- ...

[링크: Notion 현황판]
```

## 성공 기준

- [ ] 메시지가 400–800자 범위다
- [ ] 모든 섹션(긴급, 추천, 충돌, 확인 필요)이 포함된다
- [ ] Notion 링크가 포함된다
