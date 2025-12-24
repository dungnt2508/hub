"""
Leave Request Entity
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional, Literal


@dataclass
class LeaveRequest:
    """Leave request entity"""
    leave_request_id: str
    employee_id: str
    start_date: date
    end_date: date
    reason: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    approved_by: Optional[str] = None
    created_at: Optional[str] = None

