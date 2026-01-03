"""
Custom Exceptions for Router System
"""


class RouterError(Exception):
    """Base exception for router"""
    pass


class InvalidInputError(RouterError):
    """Input validation failed"""
    pass


class SessionNotFoundError(RouterError):
    """Session not found"""
    pass


class SessionCorruptedError(RouterError):
    """Session data corrupted"""
    pass


class NotFoundError(RouterError):
    """Resource not found"""
    pass


class RoutingError(RouterError):
    """Routing decision failed"""
    pass


class DomainError(RouterError):
    """Domain engine error"""
    pass


class ExternalServiceError(RouterError):
    """External service (LLM/DB/API) error"""
    pass


class RouterTimeoutError(RouterError):
    """Operation timeout"""
    pass


class ValidationError(RouterError):
    """Validation error"""
    pass


class PermissionError(RouterError):
    """Permission denied"""
    pass


class AuthenticationError(RouterError):
    """Authentication failed"""
    pass


class AuthorizationError(RouterError):
    """Authorization failed (permission denied)"""
    pass


class TenantNotFoundError(RouterError):
    """Tenant not found"""
    pass