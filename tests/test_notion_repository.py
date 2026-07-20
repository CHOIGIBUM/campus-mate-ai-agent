from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from campus_mate.config import Settings
from campus_mate.integrations.notion import PROPERTY_SCHEMA, NotionOpportunityRepository
from campus_mate.models import Opportunity, OpportunityStatus


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        NOTION_API_KEY="secret_test_only",
        NOTION_DATA_SOURCE_ID="1234567890abcdef1234567890abcdef",
        CAMPUS_MATE_DATA_DIR=tmp_path / "data",
        CAMPUS_MATE_ARTIFACTS_DIR=tmp_path / "artifacts",
    )


def _opportunity(**updates: Any) -> Opportunity:
    base: dict[str, Any] = {
        "source": "fixture",
        "source_url": "https://example.test/opportunity/1",
        "title": "AI 서비스 해커톤",
        "deadline": date(2026, 9, 30),
        "status": OpportunityStatus.RECOMMENDED,
        "fit_score": 91,
    }
    base.update(updates)
    return Opportunity(**base)


def _repo(tmp_path: Path) -> NotionOpportunityRepository:
    repo = NotionOpportunityRepository(_settings(tmp_path))
    repo._schema = {
        "properties": {
            name: {"type": next(iter(definition))}
            for name, definition in PROPERTY_SCHEMA.items()
        }
    }
    return repo


def test_query_uses_data_source_endpoint(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(method: str, path: str, *, json_body: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        calls.append((method, path, json_body))
        return {"results": [], "has_more": False}

    repo._request = request  # type: ignore[method-assign]
    assert repo._query({"filter": {"property": "공고 ID", "rich_text": {"equals": "x"}}}) == []
    assert calls[0][0] == "POST"
    assert calls[0][1] == f"/data_sources/{repo.data_source_id}/query"


def test_create_page_uses_data_source_parent_and_never_clears_existing_records(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.ensure_schema = lambda: None  # type: ignore[method-assign]
    repo._find_page = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    repo._poster_files = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(method: str, path: str, *, json_body: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        calls.append((method, path, json_body))
        assert path != "/search"
        assert method != "DELETE"
        return {"id": "page-created"}

    repo._request = request  # type: ignore[method-assign]
    stored = repo.upsert(_opportunity())

    assert stored.notion_page_id == "page-created"
    method, path, body = calls[-1]
    assert (method, path) == ("POST", "/pages")
    assert body is not None
    assert body["parent"] == {"type": "data_source_id", "data_source_id": repo.data_source_id}
    assert body["properties"]["상태"]["select"]["name"] == "Recommended"


def test_upsert_preserves_accept_status_and_calendar_ids(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.ensure_schema = lambda: None  # type: ignore[method-assign]
    repo._poster_files = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    existing_page = {"id": "page-existing", "properties": {}}
    repo._find_page = lambda *_args, **_kwargs: existing_page  # type: ignore[method-assign]
    existing = _opportunity(
        status=OpportunityStatus.ACCEPT,
        notion_page_id="page-existing",
        calendar_event_ids={"deadline": "event-1"},
    )
    repo._page_to_opportunity = lambda _page: existing  # type: ignore[method-assign]
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(method: str, path: str, *, json_body: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
        calls.append((method, path, json_body))
        return {}

    repo._request = request  # type: ignore[method-assign]
    stored = repo.upsert(_opportunity(title="수정된 제목"))

    assert stored.status == OpportunityStatus.ACCEPT
    assert stored.calendar_event_ids == {"deadline": "event-1"}
    method, path, body = calls[-1]
    assert (method, path) == ("PATCH", "/pages/page-existing")
    assert body is not None
    assert "상태" not in body["properties"]
    assert body["properties"]["공모전명"]["title"][0]["text"]["content"] == "수정된 제목"
