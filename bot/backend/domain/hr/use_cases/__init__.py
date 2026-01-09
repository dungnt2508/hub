"""
HR Domain Use Cases
"""

from .create_leave_request import CreateLeaveRequestUseCase
from .query_leave_balance import QueryLeaveBalanceUseCase
from .approve_leave import ApproveLeaveUseCase
from .query_leave_requests import QueryLeaveRequestsUseCase
from .reject_leave import RejectLeaveUseCase

__all__ = [
    "CreateLeaveRequestUseCase",
    "QueryLeaveBalanceUseCase",
    "ApproveLeaveUseCase",
    "QueryLeaveRequestsUseCase",
    "RejectLeaveUseCase",
]

