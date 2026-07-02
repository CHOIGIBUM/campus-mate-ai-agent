"""source-watchlist-crawl Skill.

Collect opportunity URLs from configured source sites and write a daily
collection JSON. This MVP uses the Python standard library only so it can run
inside the hackathon workspace without extra packages.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

KST = timezone(timedelta(hours=9))


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[Tuple[str, str]] = []
        self._active_href: Optional[str] = None
        self._text_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {k.lower(): v for k, v in attrs if k}
        href = attr_map.get("href")
        if href:
            self._active_href = href
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._active_href:
            self._text_parts.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._active_href:
            text = " ".join(part for part in self._text_parts if part)
            self.links.append((self._active_href, text))
            self._active_href = None
            self._text_parts = []


class SourceWatchlistCrawlSkill:
    """Crawl configured sources and store unique newly found URLs."""

    DEFAULT_SITES = [
        {"site_name": "링커리어", "source_url": "https://www.linkareer.com"},
        {"site_name": "씽굿", "source_url": "https://www.thinkcontest.com"},
        {"site_name": "온오프믹스", "source_url": "https://www.onoffmix.com"},
        {"site_name": "데이콘", "source_url": "https://dacon.io"},
        {"site_name": "위비티", "source_url": "https://www.wevity.com"},
        {"site_name": "강원대학교 공지", "source_url": "https://www.kangwon.ac.kr"},
        {"site_name": "강원LRS 공유대학", "source_url": "https://www.gwlrs.ac.kr"},
    ]

    OPPORTUNITY_HINTS = (
        "contest",
        "competition",
        "hackathon",
        "activity",
        "program",
        "event",
        "공모",
        "해커톤",
        "대외활동",
        "비교과",
        "교육",
        "세미나",
        "장학",
    )

    def __init__(self, collections_dir: str = "./data/collections") -> None:
        self.collections_dir = Path(collections_dir)
        self.collections_dir.mkdir(parents=True, exist_ok=True)
        self.watchlist_path = self.collections_dir / "source_watchlist.json"

    def execute(self, input_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        input_data = input_data or {}
        now = datetime.now(KST)
        sites = input_data.get("sites") or self._load_watchlist_sites() or self.DEFAULT_SITES
        existing_urls = set(input_data.get("existing_urls") or self._load_existing_urls())
        timeout = int(input_data.get("max_timeout", 30))
        max_urls_per_site = int(input_data.get("max_urls_per_site", 30))

        site_results: List[Dict[str, Any]] = []
        new_urls_all: List[Dict[str, Any]] = []

        for site in sites:
            result = self._crawl_site(site, existing_urls, timeout, max_urls_per_site, now)
            site_results.append(result)
            for item in result.get("new_urls", []):
                existing_urls.add(item["source_url"])
                new_urls_all.append(item)

        output = {
            "collection_date": now.date().isoformat(),
            "collection_time": now.isoformat(timespec="seconds"),
            "total_urls_collected": sum(r.get("all_urls_found", 0) for r in site_results),
            "unique_urls_new": len(new_urls_all),
            "site_status": site_results,
            "new_urls": new_urls_all,
        }
        self._save_daily_collection(output, now)
        self._save_watchlist(site_results, now)
        return True, f"수집 완료: 신규 URL {len(new_urls_all)}개", output

    def _crawl_site(
        self,
        site: Dict[str, Any],
        existing_urls: set[str],
        timeout: int,
        max_urls: int,
        now: datetime,
    ) -> Dict[str, Any]:
        site_name = site.get("site_name") or site.get("name") or "unknown"
        source_url = site.get("source_url") or site.get("url")
        if not source_url:
            return self._site_failure(site_name, "source_url 누락", now)

        try:
            html = site.get("html")
            if html is None:
                html = self._fetch_html(source_url, timeout)
            all_links = self._extract_links(html, source_url)
            candidates = self._filter_opportunity_links(all_links, site)
            unique_candidates = self._dedupe(candidates)
            new_urls = [
                {
                    "site_name": site_name,
                    "source_url": item["url"],
                    "title_hint": item.get("text") or "",
                    "collected_at": now.isoformat(timespec="seconds"),
                }
                for item in unique_candidates
                if item["url"] not in existing_urls
            ][:max_urls]
            return {
                "site_name": site_name,
                "source_url": source_url,
                "status": "success",
                "parse_status": "success",
                "last_success_at": now.isoformat(timespec="seconds"),
                "all_urls_found": len(all_links),
                "candidate_urls_found": len(unique_candidates),
                "new_urls": new_urls,
                "new_count": len(new_urls),
                "failure_reason": None,
            }
        except Exception as exc:  # network and parser errors should not stop the run
            return self._site_failure(site_name, str(exc), now, source_url)

    def _fetch_html(self, url: str, timeout: int) -> str:
        request = Request(url, headers={"User-Agent": "CampusCareerAI/0.1"})
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")

    def _extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        parser = LinkExtractor()
        parser.feed(html)
        links: List[Dict[str, str]] = []
        for href, text in parser.links:
            absolute = urljoin(base_url, href)
            if urlparse(absolute).scheme in {"http", "https"}:
                links.append({"url": absolute.split("#", 1)[0], "text": re.sub(r"\s+", " ", text).strip()})
        return links

    def _filter_opportunity_links(self, links: Iterable[Dict[str, str]], site: Dict[str, Any]) -> List[Dict[str, str]]:
        pattern = site.get("url_pattern")
        hints = tuple(site.get("opportunity_hints") or self.OPPORTUNITY_HINTS)
        filtered: List[Dict[str, str]] = []
        for item in links:
            haystack = f"{item.get('url', '')} {item.get('text', '')}".lower()
            if pattern and re.search(pattern, item["url"]):
                filtered.append(item)
            elif any(hint.lower() in haystack for hint in hints):
                filtered.append(item)
        return filtered

    def _dedupe(self, items: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
        seen: set[str] = set()
        deduped: List[Dict[str, str]] = []
        for item in items:
            url = item["url"]
            if url in seen:
                continue
            seen.add(url)
            deduped.append(item)
        return deduped

    def _site_failure(
        self,
        site_name: str,
        reason: str,
        now: datetime,
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "site_name": site_name,
            "source_url": source_url,
            "status": "failure",
            "parse_status": "failure",
            "last_success_at": None,
            "all_urls_found": 0,
            "candidate_urls_found": 0,
            "new_urls": [],
            "new_count": 0,
            "failure_reason": reason,
            "last_failure_at": now.isoformat(timespec="seconds"),
        }

    def _load_watchlist_sites(self) -> List[Dict[str, Any]]:
        if not self.watchlist_path.exists():
            return []
        try:
            with self.watchlist_path.open("r", encoding="utf-8") as f:
                return json.load(f).get("sites", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _load_existing_urls(self) -> List[str]:
        urls: List[str] = []
        for path in self.collections_dir.glob("daily_collection_*.json"):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                urls.extend(item.get("source_url") for item in data.get("new_urls", []) if item.get("source_url"))
            except (json.JSONDecodeError, OSError):
                continue
        return urls

    def _save_daily_collection(self, output: Dict[str, Any], now: datetime) -> None:
        path = self.collections_dir / f"daily_collection_{now.date().isoformat()}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    def _save_watchlist(self, site_results: List[Dict[str, Any]], now: datetime) -> None:
        sites = []
        for result in site_results:
            sites.append({
                "site_name": result.get("site_name"),
                "source_url": result.get("source_url"),
                "parse_status": result.get("parse_status"),
                "last_success_at": result.get("last_success_at"),
                "last_failure_at": result.get("last_failure_at"),
                "failure_reason": result.get("failure_reason"),
                "collected_count": result.get("new_count", 0),
                "updated_at": now.isoformat(timespec="seconds"),
            })
        with self.watchlist_path.open("w", encoding="utf-8") as f:
            json.dump({"sites": sites}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    ok, message, result = SourceWatchlistCrawlSkill().execute()
    print(message)
    print(json.dumps(result, ensure_ascii=False, indent=2))
