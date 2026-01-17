"""Tenant domain objects"""
from datetime import datetime
from typing import Optional
from uuid import UUID


class Tenant:
    """Tenant domain object"""
    
    def __init__(
        self,
        id: UUID,
        name: str,
        status: str,
        plan: Optional[str],
        settings_version: int,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.name = name
        self.status = status
        self.plan = plan
        self.settings_version = settings_version
        self.created_at = created_at
        self.updated_at = updated_at


class TenantSecret:
    """Tenant secret domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        type: str,
        secret_encrypted: str,
        rotated_at: Optional[datetime],
        created_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.type = type
        self.secret_encrypted = secret_encrypted
        self.rotated_at = rotated_at
        self.created_at = created_at


class Channel:
    """Channel domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        type: str,
        enabled: bool,
        config_json: Optional[dict],
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.type = type
        self.enabled = enabled
        self.config_json = config_json or {}
        self.created_at = created_at
        self.updated_at = updated_at
