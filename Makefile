.PHONY: install install-all test lint harness-check secret-scan verify demo

install:
	python -m pip install -e .

install-all:
	python -m pip install -e '.[ocr,vision,dev]'
	python -m playwright install chromium

test:
	pytest

lint:
	ruff check src tests scripts .claude/hooks

harness-check:
	python scripts/validate_harness.py

secret-scan:
	python scripts/scan_secrets.py .

verify: harness-check lint test secret-scan
	python -m compileall -q src tests scripts .claude/hooks

demo:
	CAMPUS_MATE_STORAGE_BACKEND=json campus-mate demo --fixture examples/fixtures/linkareer_detail.html
