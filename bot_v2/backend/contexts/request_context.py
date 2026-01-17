"""Request context for query processing"""
from typing import Optional
from uuid import UUID


class RequestContext:
    """Context object for request processing"""
    
    def __init__(
        self,
        tenant_id: UUID,
        channel_id: Optional[UUID] = None,
        query_text: str = ""
    ):
        self.tenant_id = tenant_id
        self.channel_id = channel_id
        self.query_text = query_text
        self.intent_name: Optional[str] = None
        self.domain: Optional[str] = None
        self.action_config: dict = {}
