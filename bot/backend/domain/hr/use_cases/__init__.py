"""
HR Domain Use Cases
"""

from .create_leave_request import CreateLeaveRequestUseCase
from .query_leave_balance import QueryLeaveBalanceUseCase
from .approve_leave import ApproveLeaveUseCase

__all__ = [
    "CreateLeaveRequestUseCase",
    "QueryLeaveBalanceUseCase",
    "ApproveLeaveUseCase",
]

