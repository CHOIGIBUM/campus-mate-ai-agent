#!/usr/bin/env python3
"""Create a new Campus Mate Notion database under NOTION_PARENT_PAGE_ID."""
from __future__ import annotations

import json
import os
import sys

import requests

from campus_mate.config import Settings
from campus_mate.integrations.notion import PROPERTY_SCHEMA


def main() -> int:
    settings = Settings()
    if not settings.notion_api_key:
        print("NOTION_API_KEY is required", file=sys.stderr)
        return 1
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "").replace("-", "").strip()
    if not parent_page_id:
        print("NOTION_PARENT_PAGE_ID is required", file=sys.stderr)
        return 1
    response = requests.post(
        "https://api.notion.com/v1/databases",
        headers={
            "Authorization": f"Bearer {settings.notion_api_key.get_secret_value()}",
            "Notion-Version": settings.notion_version,
            "Content-Type": "application/json",
        },
        json={
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "Campus Mate 공모전 현황판"}}],
            "is_inline": False,
            "icon": {"type": "emoji", "emoji": "📅"},
            "initial_data_source": {
                "title": [{"type": "text", "text": {"content": "공모전"}}],
                "properties": PROPERTY_SCHEMA,
            },
        },
        timeout=settings.request_timeout,
    )
    if response.status_code >= 400:
        print(response.text, file=sys.stderr)
        return 1
    payload = response.json()
    print(
        json.dumps(
            {
                "database_id": payload.get("id"),
                "data_sources": payload.get("data_sources", []),
                "url": payload.get("url"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
