from __future__ import annotations

from pathlib import Path
from typing import Any

from campus_mate.config import Settings
from campus_mate.integrations.base import OpportunityRepository
from campus_mate.integrations.calendar_bridge import apply_conflicts
from campus_mate.utils import read_json


def apply_freebusy(
    *,
    settings: Settings,
    repository: OpportunityRepository,
    input_path: Path,
) -> dict[str, int]:
    payload: Any = read_json(input_path)
    if payload is None:
        raise FileNotFoundError(input_path)
    return apply_conflicts(repository, payload, timezone=settings.timezone)
