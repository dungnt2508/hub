"""
Domain Engines Module
"""

from backend.domain.hr.entry_handler import HREntryHandler
from backend.domain.hr.use_cases import (
    CreateLeaveRequestUseCase,
    QueryLeaveBalanceUseCase,
    ApproveLeaveUseCase,
)
from backend.domain.catalog.entry_handler import CatalogEntryHandler

__all__ = [
    "HREntryHandler",
    "CreateLeaveRequestUseCase",
    "QueryLeaveBalanceUseCase",
    "ApproveLeaveUseCase",
    "CatalogEntryHandler",
]

