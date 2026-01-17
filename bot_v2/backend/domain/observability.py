"""Observability domain objects"""
from datetime import datetime
from typing import Optional
from uuid import UUID


class ConversationLog:
    """Conversation log domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        channel_id: Optional[UUID],
        intent: Optional[str],
        domain: Optional[str],
        success: bool,
        created_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.channel_id = channel_id
        self.intent = intent
        self.domain = domain
        self.success = success
        self.created_at = created_at


class FailedQuery:
    """Failed query domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        query: str,
        reason: Optional[str],
        created_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.query = query
        self.reason = reason
        self.created_at = created_at
