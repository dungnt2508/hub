"""
Policy Entity
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Policy:
    """Policy entity"""
    policy_id: str
    domain: str
    title: str
    content: str
    version: str
    effective_date: Optional[str] = None

