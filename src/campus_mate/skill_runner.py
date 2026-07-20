from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from campus_mate.config import Settings
from campus_mate.exceptions import CampusMateError, ConfigurationError
from campus_mate.integrations.json_repository import JsonOpportunityRepository
from campus_mate.integrations.notion import NotionOpportunityRepository
from campus_mate.integrations.slack import SlackBriefingClient
from campus_mate.models import Opportunity, ParseCandidate, SourcePage, UserProfile
from campus_mate.parsing.html import HtmlOpportunityParser
from campus_mate.parsing.merge import MultiPassParser
from campus_mate.parsing.ocr import OcrOpportunityParser
from campus_mate.parsing.vision import PosterVisionParser
from campus_mate.services.keywords import expand_keywords
from campus_mate.services.onboarding import OnboardingService
from campus_mate.services.recommendation import RecommendationEngine
from campus_mate.sources.linkareer import LinkareerSource
from campus_mate.utils import atomic_write_json, now_in_timezone
from campus_mate.workflows.accept_sync import apply_calendar_results, plan_calendar_requests
from campus_mate.workflows.brief import create_briefing
from campus_mate.workflows.conflicts import apply_freebusy


def _candidate_dump(candidate: ParseCandidate) -> dict[str, Any]:
    return candidate.model_dump(mode="json")


def _write_or_print(payload: Any, output: Path | None) -> None:
    if output:
        atomic_write_json(output, payload)
        print(str(output))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_profile(path: Path) -> UserProfile:
    return UserProfile.model_validate_json(path.read_text(encoding="utf-8"))


def _load_opportunity(path: Path) -> Opportunity:
    return Opportunity.model_validate_json(path.read_text(encoding="utf-8"))


def _repository(settings: Settings):
    if settings.storage_backend == "notion":
        return NotionOpportunityRepository(settings)
    return JsonOpportunityRepository(settings.local_store_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="campus-mate-skill",
        description="Atomic code entry points used by Campus Mate Claude skills.",
    )
    parser.add_argument("--storage", choices=("notion", "json"))
    sub = parser.add_subparsers(dest="skill", required=True)

    profile = sub.add_parser("profile-build")
    profile.add_argument("--input", type=Path, required=True)
    profile.add_argument("--output", type=Path, default=Path("data/user_profile.json"))

    crawl = sub.add_parser("source-watchlist-crawl")
    crawl.add_argument("--source", choices=("linkareer",), default="linkareer")
    crawl.add_argument("--limit", type=int, default=8)
    crawl.add_argument("--output", type=Path)

    html = sub.add_parser("html-opportunity-parse")
    html.add_argument("--html", type=Path, required=True)
    html.add_argument("--url", required=True)
    html.add_argument("--source", default="fixture")
    html.add_argument("--poster-url")
    html.add_argument("--output", type=Path)

    ocr = sub.add_parser("rendered-page-ocr")
    group = ocr.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=Path)
    group.add_argument("--url")
    ocr.add_argument("--output", type=Path)

    vision = sub.add_parser("poster-vision-extract")
    vision.add_argument("--image", type=Path, required=True)
    vision.add_argument("--mime-type", default="image/jpeg")
    vision.add_argument("--output", type=Path)

    merge = sub.add_parser("schema-merge-and-validate")
    merge.add_argument("--html", type=Path, required=True)
    merge.add_argument("--url", required=True)
    merge.add_argument("--source", default="fixture")
    merge.add_argument("--poster-url")
    merge.add_argument("--all-passes", action="store_true")
    merge.add_argument("--output", type=Path)

    keywords = sub.add_parser("interest-keyword-expand")
    keywords.add_argument("--profile", type=Path, required=True)
    keywords.add_argument("--output", type=Path)

    score = sub.add_parser("fit-score-rank")
    score.add_argument("--profile", type=Path, required=True)
    score.add_argument("--opportunity", type=Path, required=True)
    score.add_argument("--today", type=date.fromisoformat)
    score.add_argument("--output", type=Path)

    priority = sub.add_parser("deadline-priority-rank")
    priority.add_argument("--profile", type=Path, required=True)
    priority.add_argument("--opportunity", type=Path, required=True)
    priority.add_argument("--today", type=date.fromisoformat)
    priority.add_argument("--output", type=Path)

    notion = sub.add_parser("notion-dashboard-sync")
    notion.add_argument("--opportunity", type=Path, required=True)
    notion.add_argument("--output", type=Path)

    freebusy = sub.add_parser("calendar-freebusy-check")
    freebusy.add_argument("--input", type=Path, required=True)
    freebusy.add_argument("--output", type=Path)

    calendar = sub.add_parser("calendar-event-create")
    calendar.add_argument("--output", type=Path, default=Path("artifacts/calendar_requests.json"))

    accept = sub.add_parser("accept-state-sync")
    accept.add_argument("--requests", type=Path, required=True)
    accept.add_argument("--results", type=Path, required=True)
    accept.add_argument("--output", type=Path)

    slack = sub.add_parser("slack-brief-generate")
    slack.add_argument("--dry-run", action="store_true")
    slack.add_argument("--artifact", type=Path)
    slack.add_argument("--output", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = Settings()
        if args.storage:
            settings.storage_backend = args.storage
        settings.ensure_directories()

        if args.skill == "profile-build":
            service = OnboardingService(args.output)
            profile = service.import_json_text(args.input.read_text(encoding="utf-8"))
            _write_or_print(profile.model_dump(mode="json"), args.output)
            return 0

        if args.skill == "source-watchlist-crawl":
            source = LinkareerSource(settings)
            urls = source.discover(args.limit)
            payload = {
                "source": source.name,
                "discovered_at": now_in_timezone(settings.timezone).isoformat(),
                "count": len(urls),
                "urls": urls,
            }
            _write_or_print(payload, args.output)
            return 0

        if args.skill == "html-opportunity-parse":
            page = SourcePage(
                source=args.source,
                url=args.url,
                html=args.html.read_text(encoding="utf-8"),
                fetched_at=now_in_timezone(settings.timezone),
                poster_url=args.poster_url,
            )
            payload = _candidate_dump(HtmlOpportunityParser().parse(page))
            _write_or_print(payload, args.output)
            return 0

        if args.skill == "rendered-page-ocr":
            ocr = OcrOpportunityParser(settings)
            if args.image:
                candidate = ocr.extract_image(args.image.read_bytes())
                screenshot = None
            else:
                candidate, screenshot = ocr.extract_rendered_page(args.url)
            payload = _candidate_dump(candidate)
            payload["screenshot_captured"] = bool(screenshot)
            _write_or_print(payload, args.output)
            return 0

        if args.skill == "poster-vision-extract":
            candidate = PosterVisionParser(settings).extract(
                args.image.read_bytes(), mime_type=args.mime_type
            )
            _write_or_print(_candidate_dump(candidate), args.output)
            return 0

        if args.skill == "schema-merge-and-validate":
            page = SourcePage(
                source=args.source,
                url=args.url,
                html=args.html.read_text(encoding="utf-8"),
                fetched_at=now_in_timezone(settings.timezone),
                poster_url=args.poster_url,
            )
            opportunity = MultiPassParser(settings).parse(page, force_all_passes=args.all_passes)
            _write_or_print(opportunity.model_dump(mode="json"), args.output)
            return 0

        if args.skill == "interest-keyword-expand":
            profile = _load_profile(args.profile)
            payload = {"terms": expand_keywords(profile), "source_profile": str(args.profile)}
            _write_or_print(payload, args.output)
            return 0

        if args.skill in {"fit-score-rank", "deadline-priority-rank"}:
            profile = _load_profile(args.profile)
            opportunity = _load_opportunity(args.opportunity)
            today = args.today or now_in_timezone(settings.timezone).date()
            recommendation = RecommendationEngine().score(opportunity, profile, today=today)
            payload = recommendation.model_dump(mode="json")
            if args.skill == "deadline-priority-rank":
                payload = {
                    "priority": recommendation.priority.value,
                    "days_until_deadline": recommendation.days_until_deadline,
                    "score": recommendation.score,
                }
            _write_or_print(payload, args.output)
            return 0

        repository = _repository(settings)

        if args.skill == "notion-dashboard-sync":
            if settings.storage_backend != "notion":
                raise ConfigurationError("notion-dashboard-sync requires --storage notion")
            stored = repository.upsert(_load_opportunity(args.opportunity))
            _write_or_print(stored.model_dump(mode="json"), args.output)
            return 0

        if args.skill == "calendar-freebusy-check":
            result = apply_freebusy(settings=settings, repository=repository, input_path=args.input)
            _write_or_print(result, args.output)
            return 0

        if args.skill == "calendar-event-create":
            count = plan_calendar_requests(
                settings=settings, repository=repository, output_path=args.output
            )
            print(json.dumps({"requests": count, "output": str(args.output)}, ensure_ascii=False))
            return 0

        if args.skill == "accept-state-sync":
            result = apply_calendar_results(
                repository=repository,
                requests_path=args.requests,
                results_path=args.results,
            )
            _write_or_print(result, args.output)
            return 0 if result.get("errors", 0) == 0 else 2

        if args.skill == "slack-brief-generate":
            report = create_briefing(
                settings=settings,
                repository=repository,
                slack=SlackBriefingClient(settings),
                dry_run=args.dry_run,
                output_path=args.artifact,
            )
            _write_or_print(report.model_dump(mode="json"), args.output)
            return 0

        parser.error("Unhandled skill")
        return 2
    except (CampusMateError, ValidationError, FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
