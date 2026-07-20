from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from campus_mate.config import Settings
from campus_mate.exceptions import IntegrationError
from campus_mate.models import SourcePage
from campus_mate.utils import build_retry_session, normalize_url, now_in_timezone

LOGGER = logging.getLogger(__name__)


class LinkareerSource:
    name = "링커리어"
    listing_url = "https://linkareer.com/list/contest"
    base_url = "https://linkareer.com"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = build_retry_session(
            settings.max_retries,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36 "
                "CampusMate/1.0"
            ),
        )

    def discover(self, limit: int) -> list[str]:
        response = self.session.get(self.listing_url, timeout=self.settings.request_timeout)
        if response.status_code >= 400:
            raise IntegrationError(
                f"Linkareer listing request failed ({response.status_code}): {self.listing_url}"
            )
        soup = BeautifulSoup(response.text, "html.parser")
        urls: list[str] = []
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = str(anchor["href"])
            if not re.match(r"^/activity/\d+", href):
                continue
            url = normalize_url(urljoin(self.base_url, href))
            if url not in seen:
                seen.add(url)
                urls.append(url)
            if len(urls) >= limit:
                break
        LOGGER.info("Discovered %d Linkareer URLs", len(urls))
        return urls

    def fetch(self, url: str) -> SourcePage:
        response = self.session.get(url, timeout=self.settings.request_timeout)
        if response.status_code >= 400:
            raise IntegrationError(f"Linkareer detail request failed ({response.status_code}): {url}")
        soup = BeautifulSoup(response.text, "html.parser")
        poster = soup.find("meta", property="og:image")
        poster_url = str(poster.get("content", "")).strip() if poster else None
        return SourcePage(
            source=self.name,
            url=normalize_url(response.url or url),
            html=response.text,
            fetched_at=now_in_timezone(self.settings.timezone),
            poster_url=poster_url or None,
        )
