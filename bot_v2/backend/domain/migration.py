"""Migration domain objects"""
from datetime import datetime
from typing import Optional
from uuid import UUID


class MigrationJob:
    """Migration job domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        source_type: str,
        status: str,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.source_type = source_type
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at


class MigrationVersion:
    """Migration version domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        version: int,
        approved_by: Optional[str],
        approved_at: Optional[datetime],
        created_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.version = version
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.created_at = created_at
