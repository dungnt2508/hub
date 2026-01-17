"""Intent domain objects"""
from datetime import datetime
from typing import Optional
from uuid import UUID


class Intent:
    """Intent domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        name: str,
        domain: str,
        priority: int,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.domain = domain
        self.priority = priority
        self.created_at = created_at
        self.updated_at = updated_at


class IntentPattern:
    """Intent pattern domain object"""
    
    def __init__(
        self,
        id: UUID,
        intent_id: UUID,
        type: str,
        pattern: str,
        weight: float,
        created_at: datetime
    ):
        self.id = id
        self.intent_id = intent_id
        self.type = type  # keyword, regex, phrase
        self.pattern = pattern
        self.weight = weight
        self.created_at = created_at


class IntentHint:
    """Intent hint domain object"""
    
    def __init__(
        self,
        id: UUID,
        intent_id: UUID,
        hint_text: str,
        created_at: datetime
    ):
        self.id = id
        self.intent_id = intent_id
        self.hint_text = hint_text
        self.created_at = created_at


class IntentAction:
    """Intent action domain object"""
    
    def __init__(
        self,
        id: UUID,
        intent_id: UUID,
        action_type: str,
        config_json: Optional[dict],
        priority: int,
        created_at: datetime
    ):
        self.id = id
        self.intent_id = intent_id
        self.action_type = action_type  # query_db, handoff, refuse, rag
        self.config_json = config_json or {}
        self.priority = priority
        self.created_at = created_at
