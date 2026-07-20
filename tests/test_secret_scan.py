from pathlib import Path


def test_repository_contains_no_known_real_token_patterns() -> None:
    root = Path(__file__).resolve().parents[1]
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".md", ".toml", ".json", ".example"}
    )
    assert ("xoxb" + "-115028") not in text
    assert ("ntn" + "_269943") not in text
