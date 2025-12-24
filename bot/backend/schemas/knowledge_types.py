"""
Knowledge Engine Type Definitions
"""
from typing import Optional, Literal, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class KnowledgeRequest:
    """Knowledge engine input request"""
    question: str
    domain: str
    context: Optional[Dict[str, Any]] = None
    trace_id: str = ""

    def __post_init__(self):
        """Validate knowledge request"""
        if not self.question or not self.question.strip():
            raise ValueError("question is required and non-empty")
        if not self.domain:
            raise ValueError("domain is required")
        if not self.trace_id:
            raise ValueError("trace_id is required")


@dataclass
class KnowledgeSource:
    """Knowledge source citation"""
    title: str
    url: Optional[str] = None
    page: Optional[int] = None
    excerpt: Optional[str] = None


@dataclass
class KnowledgeResponse:
    """Knowledge engine output response"""
    answer: str
    citations: List[str]
    confidence: float
    sources: Optional[List[KnowledgeSource]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate knowledge response"""
        if not self.answer or not self.answer.strip():
            raise ValueError("answer is required and non-empty")
        if not self.citations:
            raise ValueError("citations is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

