from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from dateutil import parser as date_parser
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def now_in_timezone(timezone: str) -> datetime:
    return datetime.now(ZoneInfo(timezone))


def normalize_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    path = re.sub(r"/+", "/", parts.path).rstrip("/") or "/"
    query_parts = [piece for piece in parts.query.split("&") if piece and not piece.startswith("utm_")]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "&".join(query_parts), ""))


def stable_identifier(*parts: str, length: int = 24) -> str:
    payload = "\x1f".join(part.strip() for part in parts if part is not None)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def compact_text(value: str | None, limit: int = 1900) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    return text[:limit]


def parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, (int, float)):
        number = float(value)
        if number > 10_000_000_000:
            number /= 1000
        try:
            return datetime.fromtimestamp(number).date()
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("년", "-").replace("월", "-").replace("일", "")
    text = re.sub(r"[./]", "-", text)
    text = re.sub(r"\([^)]*\)", "", text)
    text = text.strip(" ~부터까지")
    try:
        parsed = date_parser.parse(text, fuzzy=True, dayfirst=False)
        return parsed.date()
    except (ValueError, TypeError, OverflowError):
        return None


def build_retry_session(max_retries: int = 3, user_agent: str | None = None) -> Session:
    retry = Retry(
        total=max_retries,
        connect=max_retries,
        read=max_retries,
        status=max_retries,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST", "PATCH", "PUT", "DELETE"}),
        respect_retry_after_header=True,
    )
    session = Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    if user_agent:
        session.headers.update({"User-Agent": user_agent})
    return session


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=_json_default)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime, Path)):
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
