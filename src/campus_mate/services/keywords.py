from __future__ import annotations

from campus_mate.models import UserProfile

# Conservative aliases used only to broaden recall. They do not change the user's profile.
_KEYWORD_ALIASES: dict[str, tuple[str, ...]] = {
    "인공지능": ("AI", "머신러닝", "딥러닝"),
    "ai": ("인공지능", "머신러닝", "딥러닝"),
    "데이터": ("데이터분석", "데이터사이언스", "빅데이터"),
    "헬스케어": ("디지털헬스", "의료AI", "의료데이터"),
    "의료": ("헬스케어", "의료AI", "의료데이터"),
    "창업": ("스타트업", "비즈니스", "사업화"),
    "기획": ("서비스기획", "프로덕트", "PM"),
    "개발": ("소프트웨어", "프로그래밍", "백엔드", "프론트엔드"),
    "디자인": ("UX", "UI", "콘텐츠"),
    "보안": ("사이버보안", "정보보호"),
    "환경": ("기후", "탄소중립", "ESG"),
}


def expand_keywords(profile: UserProfile) -> list[str]:
    """Return stable, de-duplicated recommendation/search terms.

    The returned list includes user-provided terms first, then conservative aliases. No alias is
    written back to the original profile unless the caller explicitly chooses to do so.
    """

    raw = [profile.major, profile.career_goal, *profile.interests, *profile.keywords]
    output: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        text = value.strip()
        if not text:
            return
        key = text.casefold()
        if key in seen:
            return
        seen.add(key)
        output.append(text)

    for value in raw:
        add(value)
        for token in value.replace("·", " ").replace("/", " ").replace("-", " ").split():
            add(token)
            aliases = _KEYWORD_ALIASES.get(token.casefold(), ())
            for alias in aliases:
                add(alias)
    return output
