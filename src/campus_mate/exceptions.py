class CampusMateError(Exception):
    """Base exception for expected Campus Mate failures."""


class ConfigurationError(CampusMateError):
    """Raised when required runtime configuration is missing or invalid."""


class IntegrationError(CampusMateError):
    """Raised when an external service returns an unrecoverable error."""


class ParseError(CampusMateError):
    """Raised when a notice cannot be parsed into a minimally valid record."""


class StateTransitionError(CampusMateError):
    """Raised when a status transition would violate the workflow state machine."""
