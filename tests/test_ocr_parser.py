from campus_mate.parsing.ocr import OcrOpportunityParser


def test_ocr_text_parser_extracts_labels(settings) -> None:
    parser = OcrOpportunityParser(settings)
    result = parser.parse_text(
        """
        2026 AI·DATA 대학생 해커톤
        주최: 강원 AI 센터
        참가 자격: 전국 대학생 및 대학원생
        접수 마감: 2026년 9월 30일
        시상: 대상 500만원
        """
    )
    assert "AI·DATA" in result.values["title"]
    assert result.values["organization"] == "강원 AI 센터"
    assert result.values["deadline"].isoformat() == "2026-09-30"
