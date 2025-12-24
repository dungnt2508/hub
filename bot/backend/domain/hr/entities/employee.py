"""
Employee Entity
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Employee:
    """Employee entity"""
    employee_id: str
    user_id: str
    name: str
    email: str
    department: str
    leave_balance: int = 0
    role: Optional[str] = None

