from __future__ import annotations

from typing import Protocol

from campus_mate.models import SourcePage


class OpportunitySource(Protocol):
    name: str

    def discover(self, limit: int) -> list[str]: ...

    def fetch(self, url: str) -> SourcePage: ...
