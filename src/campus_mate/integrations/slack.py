from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import requests

from campus_mate.config import Settings
from campus_mate.exceptions import IntegrationError
from campus_mate.models import Opportunity
from campus_mate.utils import atomic_write_json, build_retry_session

LOGGER = logging.getLogger(__name__)


class SlackBriefingClient:
    API_URL = "https://slack.com/api/chat.postMessage"

    def __init__(self, settings: Settings, session: requests.Session | None = None):
        self.settings = settings
        self.session = session or build_retry_session(settings.max_retries)

    def build_message(self, opportunities: list[Opportunity], *, today: date) -> dict[str, Any]:
        rows = sorted(
            opportunities,
            key=lambda item: (item.fit_score or 0, item.deadline or date.max),
            reverse=True,
        )
        urgent = [item for item in rows if _days_until(item, today) is not None and 0 <= _days_until(item, today) <= 7]
        conflicts = [item for item in rows if item.conflict_status.value == "있음"]
        top = rows[:5]
        fallback = (
            f"Campus Mate 브리핑: 추천 {len(rows)}건, 마감 임박 {len(urgent)}건, "
            f"일정 충돌 {len(conflicts)}건"
        )
        blocks: list[dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📬 오늘의 공모전 브리핑 ({today:%m/%d})",
                    "emoji": True,
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            f"추천 *{len(rows)}건* · 마감 임박 *{len(urgent)}건* · "
                            f"일정 충돌 *{len(conflicts)}건*"
                        ),
                    }
                ],
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*🏆 추천 TOP*"}},
        ]
        icon = {"긴급": "🔴", "중요": "🟡", "참고": "⚪"}
        if not top:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "오늘 새로 추천할 공고가 없습니다."},
                }
            )
        for item in top:
            days = _days_until(item, today)
            deadline_text = "마감일 미확인" if days is None else (f"D-{days}" if days >= 0 else "마감")
            conflict = " · ⚠️ 일정 충돌" if item.conflict_status.value == "있음" else ""
            link = f"<{item.source_url}|원문>" if item.source_url else "원문 없음"
            reasons = " · ".join(item.recommendation_reasons[:3]) or "프로필 기반 추천"
            priority = item.priority.value if item.priority else "참고"
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"{icon.get(priority, '⚪')} *{item.title[:80]}*\n"
                            f"적합도 {item.fit_score or 0}점 · {deadline_text} · {link}{conflict}\n"
                            f"_{reasons[:180]}_"
                        ),
                    },
                }
            )
        if urgent:
            blocks.extend(
                [
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*⏰ 마감 임박 (D-7 이내)*\n"
                            + "\n".join(
                                f"• {item.title[:70]} (D-{_days_until(item, today)})"
                                for item in urgent[:10]
                            ),
                        },
                    },
                ]
            )
        if conflicts:
            blocks.extend(
                [
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*⚠️ 기존 일정과 충돌*\n"
                            + "\n".join(f"• {item.title[:70]}" for item in conflicts[:10]),
                        },
                    },
                ]
            )
        dashboard_url = self.settings.notion_dashboard_url
        if dashboard_url:
            blocks.extend(
                [
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"👉 <{dashboard_url}|Notion 현황판에서 확인>하고 참가할 공고의 "
                                "상태를 *Accept*로 바꾸면 Google Calendar에 반영됩니다."
                            ),
                        },
                    },
                ]
            )
        return {"text": fallback, "blocks": blocks}

    def send(self, message: dict[str, Any]) -> dict[str, Any]:
        self.settings.require_slack()
        assert self.settings.slack_bot_token is not None
        response = self.session.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.settings.slack_bot_token.get_secret_value()}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"channel": self.settings.slack_channel_id, **message},
            timeout=self.settings.request_timeout,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationError("Slack returned a non-JSON response") from exc
        if response.status_code >= 400 or not payload.get("ok"):
            raise IntegrationError(
                f"Slack chat.postMessage failed: {payload.get('error') or response.status_code}"
            )
        return payload

    def write_dry_run(self, message: dict[str, Any], path: Path) -> None:
        atomic_write_json(path, message)
        LOGGER.info("Slack dry-run payload written to %s", path)


def _days_until(item: Opportunity, today: date) -> int | None:
    if not item.deadline:
        return None
    return (item.deadline - today).days
