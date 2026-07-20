from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from campus_mate.config import Settings
from campus_mate.exceptions import CampusMateError, ConfigurationError
from campus_mate.integrations.base import OpportunityRepository
from campus_mate.integrations.json_repository import JsonOpportunityRepository
from campus_mate.integrations.notion import NotionOpportunityRepository
from campus_mate.integrations.slack import SlackBriefingClient
from campus_mate.logging_config import configure_logging
from campus_mate.models import OpportunityStatus
from campus_mate.parsing.merge import MultiPassParser
from campus_mate.services.onboarding import OnboardingService
from campus_mate.sources.linkareer import LinkareerSource
from campus_mate.utils import atomic_write_json
from campus_mate.workflows.accept_sync import apply_calendar_results, plan_calendar_requests
from campus_mate.workflows.brief import create_briefing
from campus_mate.workflows.collect import collect_opportunities
from campus_mate.workflows.conflicts import apply_freebusy
from campus_mate.workflows.demo import run_fixture_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="campus-mate",
        description="Campus Mate Timely-orchestrated notice collection and schedule workflow",
    )
    parser.add_argument("--storage", choices=("notion", "json"), help="Override storage backend")
    parser.add_argument("--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    profile = sub.add_parser("profile", help="Create or inspect the recommendation profile")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_sub.add_parser("init", help="Interactive onboarding")
    profile_import = profile_sub.add_parser("import", help="Import profile JSON")
    profile_import.add_argument("--file", type=Path, help="JSON file; stdin is used when omitted")
    profile_sub.add_parser("show", help="Print the stored profile")

    notion = sub.add_parser("notion", help="Notion schema operations")
    notion_sub = notion.add_subparsers(dest="notion_command", required=True)
    notion_sub.add_parser("ensure-schema", help="Add missing Campus Mate properties")

    collect = sub.add_parser("collect", help="Collect, parse, score, and upsert notices")
    collect.add_argument("--source", choices=("linkareer",), default="linkareer")
    collect.add_argument("--limit", type=int)
    collect.add_argument("--all-passes", action="store_true", help="Run OCR and vision even when HTML is complete")
    collect.add_argument("--report", type=Path)

    brief = sub.add_parser("brief", help="Create the daily Slack briefing")
    brief.add_argument("--dry-run", action="store_true")
    brief.add_argument("--output", type=Path)

    conflicts = sub.add_parser("conflicts", help="Apply Google Calendar busy intervals")
    conflicts_sub = conflicts.add_subparsers(dest="conflicts_command", required=True)
    conflicts_apply = conflicts_sub.add_parser("apply")
    conflicts_apply.add_argument("--input", type=Path, required=True)

    calendar = sub.add_parser("calendar", help="Timely/Composio calendar manifest bridge")
    calendar_sub = calendar.add_subparsers(dest="calendar_command", required=True)
    calendar_plan = calendar_sub.add_parser("plan")
    calendar_plan.add_argument("--output", type=Path, default=Path("artifacts/calendar_requests.json"))
    calendar_apply = calendar_sub.add_parser("apply")
    calendar_apply.add_argument("--requests", type=Path, default=Path("artifacts/calendar_requests.json"))
    calendar_apply.add_argument("--results", type=Path, default=Path("artifacts/calendar_results.json"))

    demo = sub.add_parser("demo", help="Run a deterministic fixture-based end-to-end demo")
    demo.add_argument("--fixture", type=Path, required=True)
    demo.add_argument("--output", type=Path, default=Path("artifacts/demo_result.json"))

    listing = sub.add_parser("list", help="List stored opportunities")
    listing.add_argument("--status", choices=[status.value for status in OpportunityStatus])

    return parser


def make_repository(settings: Settings) -> OpportunityRepository:
    if settings.storage_backend == "notion":
        return NotionOpportunityRepository(settings)
    return JsonOpportunityRepository(settings.local_store_path)


def _settings(args: argparse.Namespace) -> Settings:
    settings = Settings()
    if args.storage:
        settings.storage_backend = args.storage
    if args.verbose:
        settings.log_level = "DEBUG"
    settings.ensure_directories()
    return settings


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = _settings(args)
        configure_logging(settings.log_level)
        onboarding = OnboardingService(settings.profile_path)

        if args.command == "profile":
            if args.profile_command == "init":
                onboarding.interactive()
                return 0
            if args.profile_command == "import":
                text = args.file.read_text(encoding="utf-8") if args.file else sys.stdin.read()
                profile = onboarding.import_json_text(text)
                print(onboarding.summary(profile))
                return 0
            if args.profile_command == "show":
                profile = onboarding.load()
                print(json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, indent=2))
                return 0

        repository = make_repository(settings)

        if args.command == "notion":
            if settings.storage_backend != "notion":
                raise ConfigurationError("Use --storage notion for Notion schema operations.")
            repository.ensure_schema()
            print("Notion data source schema is ready.")
            return 0

        if args.command == "collect":
            profile = onboarding.load()
            source = LinkareerSource(settings)
            report = collect_opportunities(
                settings=settings,
                repository=repository,
                source=source,
                parser=MultiPassParser(settings),
                profile=profile,
                limit=args.limit or settings.source_limit,
                force_all_passes=args.all_passes,
                report_path=args.report,
            )
            print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return 0 if report.failures == 0 else 2

        if args.command == "brief":
            report = create_briefing(
                settings=settings,
                repository=repository,
                slack=SlackBriefingClient(settings),
                dry_run=args.dry_run,
                output_path=args.output,
            )
            print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return 0

        if args.command == "conflicts" and args.conflicts_command == "apply":
            result = apply_freebusy(settings=settings, repository=repository, input_path=args.input)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "calendar":
            if args.calendar_command == "plan":
                count = plan_calendar_requests(
                    settings=settings, repository=repository, output_path=args.output
                )
                print(json.dumps({"requests": count, "output": str(args.output)}, ensure_ascii=False))
                return 0
            if args.calendar_command == "apply":
                result = apply_calendar_results(
                    repository=repository,
                    requests_path=args.requests,
                    results_path=args.results,
                )
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0 if result["errors"] == 0 else 2

        if args.command == "demo":
            profile = onboarding.load()
            result = run_fixture_demo(
                settings=settings,
                repository=repository,
                fixture_path=args.fixture,
                profile=profile,
            )
            atomic_write_json(args.output, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "list":
            if args.status:
                items = repository.list_by_status([OpportunityStatus(args.status)])
            else:
                items = repository.list_all()
            print(json.dumps([item.model_dump(mode="json") for item in items], ensure_ascii=False, indent=2))
            return 0

        parser.error("Unhandled command")
        return 2
    except (CampusMateError, ValidationError, FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
