"""Core shared module - Base classes, exceptions, logger, utils"""
from app.core.shared.base_entity import BaseEntity, AggregateRoot, ValueObject
from app.core.shared.base_repository import BaseRepository, ReadOnlyRepository
from app.core.shared.base_usecase import BaseUseCase, BaseQueryUseCase, BaseCommandUseCase
from app.core.shared.exceptions import (
    BaseException,
    DomainException,
    ApplicationException,
    InfrastructureException,
    InterfaceException,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidStateError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    UseCaseError,
    DatabaseError,
    CacheError,
    ExternalServiceError,
    AIModelError,
    VectorStoreError,
    InvalidRequestError,
    ResourceNotFoundError,
)
from app.core.shared.logger import get_logger, configure_logger, LoggerMixin

__all__ = [
    # Base classes
    "BaseEntity",
    "AggregateRoot",
    "ValueObject",
    "BaseRepository",
    "ReadOnlyRepository",
    "BaseUseCase",
    "BaseQueryUseCase",
    "BaseCommandUseCase",
    # Exceptions
    "BaseException",
    "DomainException",
    "ApplicationException",
    "InfrastructureException",
    "InterfaceException",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "BusinessRuleViolationError",
    "InvalidStateError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "UseCaseError",
    "DatabaseError",
    "CacheError",
    "ExternalServiceError",
    "AIModelError",
    "VectorStoreError",
    "InvalidRequestError",
    "ResourceNotFoundError",
    # Logger
    "get_logger",
    "configure_logger",
    "LoggerMixin",
]

