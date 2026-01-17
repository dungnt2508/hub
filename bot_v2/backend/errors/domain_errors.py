"""Domain-specific exceptions"""


class IntentNotFoundError(Exception):
    """Raised when no intent matches the query"""
    pass


class GuardrailViolationError(Exception):
    """Raised when query violates guardrails"""
    
    def __init__(self, message: str, fallback_message: str):
        super().__init__(message)
        self.fallback_message = fallback_message


class DataNotFoundError(Exception):
    """Raised when requested data is not found in database"""
    pass


class NoActionConfiguredError(Exception):
    """Raised when intent has no configured actions"""
    pass
