"""interest-keyword-expand Skill."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple


class InterestKeywordExpandSkill:
    """Expand user interests into deterministic Korean/English keyword sets."""

    DEFAULT_EXPANSIONS = {
        "의료AI": ["의료AI", "헬스케어", "의료 데이터", "바이오", "medical AI", "healthcare", "health tech"],
        "데이터 분석": ["데이터 분석", "빅데이터", "데이터 사이언스", "통계", "data analysis", "data science"],
        "AI Agent": ["AI Agent", "에이전트", "자동화", "LLM", "챗봇", "agentic", "automation"],
        "자연언어처리": ["자연언어처리", "NLP", "LLM", "텍스트 분석", "language model"],
        "컴퓨터비전": ["컴퓨터비전", "이미지", "영상", "OCR", "computer vision"],
        "웹 개발": ["웹", "프론트엔드", "백엔드", "React", "Django", "web development"],
        "보안": ["보안", "정보보호", "해킹", "CTF", "cybersecurity"],
        "머신러닝": ["머신러닝", "ML", "모델링", "예측", "machine learning"],
        "딥러닝": ["딥러닝", "deep learning", "신경망", "모델 학습"],
    }

    def execute(self, input_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        profile = input_data.get("user_profile") or {}
        base_fields = input_data.get("base_fields")
        if base_fields is None:
            base_fields = profile.get("interests", {}).get("fields", [])
        expanded: Dict[str, List[str]] = {}
        for field in base_fields:
            values = self.DEFAULT_EXPANSIONS.get(field, [field])
            expanded[field] = list(dict.fromkeys([field, *values]))
        flattened = []
        for values in expanded.values():
            flattened.extend(values)
        output = {
            "user_id": input_data.get("user_id") or profile.get("user_id"),
            "expanded_keywords": expanded,
            "all_keywords_flattened": list(dict.fromkeys(flattened)),
        }
        return True, f"키워드 확장 완료: {len(output['all_keywords_flattened'])}개", output


if __name__ == "__main__":
    import sys

    stdin_text = sys.stdin.read()
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    ok, message, output = InterestKeywordExpandSkill().execute(payload)
    print(message)
    print(json.dumps(output, ensure_ascii=False, indent=2))
