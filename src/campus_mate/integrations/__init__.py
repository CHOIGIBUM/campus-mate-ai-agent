from .base import OpportunityRepository
from .json_repository import JsonOpportunityRepository
from .notion import NotionOpportunityRepository
from .slack import SlackBriefingClient

__all__ = [
    "OpportunityRepository",
    "JsonOpportunityRepository",
    "NotionOpportunityRepository",
    "SlackBriefingClient",
]
