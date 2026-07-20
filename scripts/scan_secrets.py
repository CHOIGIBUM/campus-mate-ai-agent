#!/usr/bin/env python3
"""Fail when common credential patterns are found in repository text files."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = {
    "Slack token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "Notion token": re.compile(r"(?:secret|ntn)_[A-Za-z0-9]{20,}"),
    "Private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Generic bearer": re.compile(r"Bearer\s+[A-Za-z0-9._-]{30,}"),
}
SKIP_DIRS = {".git", ".venv", "venv", "dist", "build", "__pycache__"}
TEXT_SUFFIXES = {".py", ".md", ".toml", ".txt", ".json", ".yaml", ".yml", ".env", ".example"}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == ".env.example":
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {".env", ".gitignore"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(root)}:{line}: {name}")
    if findings:
        print("Potential secrets found:")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("No common credential patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
