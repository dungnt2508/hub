from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.base import BaseRepository

# Infrastructure Models
from app.infrastructure.database.models.knowledge import MigrationJob as MigrationModel

# Domain Entities
from app.core import domain


class MigrationJobRepository(BaseRepository[MigrationModel]):
    """Repository for MigrationJob with Domain Mapping"""
    domain_container = domain.MigrationJob
    
    def __init__(self, db: AsyncSession):
        super().__init__(MigrationModel, db)
