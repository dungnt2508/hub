"""Repositories for data access"""
from backend.repositories.tenant_repository import TenantRepository
from backend.repositories.catalog_repository import CatalogRepository
from backend.repositories.intent_repository import IntentRepository
from backend.repositories.migration_repository import MigrationRepository
from backend.repositories.observability_repository import ObservabilityRepository

__all__ = [
    "TenantRepository",
    "CatalogRepository",
    "IntentRepository",
    "MigrationRepository",
    "ObservabilityRepository",
]
