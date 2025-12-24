"""
Admin Knowledge API - Endpoints for managing knowledge base
"""
from typing import Dict, Any, Optional

from ..knowledge.catalog_knowledge_sync import CatalogKnowledgeSyncService
from ..domain.tenant.tenant_service import TenantService
from ..shared.logger import logger
from ..shared.exceptions import TenantNotFoundError, InvalidInputError


class AdminKnowledgeAPI:
    """
    Admin API endpoints for knowledge base management.
    
    Endpoints:
    - POST /admin/tenants/{tenant_id}/knowledge/sync
    - GET /admin/tenants/{tenant_id}/knowledge/status
    - DELETE /admin/tenants/{tenant_id}/knowledge
    """
    
    def __init__(self, db_connection):
        """
        Initialize admin knowledge API.
        
        Args:
            db_connection: PostgreSQL connection pool
        """
        self.db = db_connection
        self.sync_service = CatalogKnowledgeSyncService(db_connection)
        self.tenant_service = TenantService(db_connection)
        logger.info("AdminKnowledgeAPI initialized")
    
    async def sync_knowledge(
        self,
        tenant_id: str,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """
        POST /admin/tenants/{tenant_id}/knowledge/sync
        
        Trigger manual sync of knowledge base for tenant.
        
        Args:
            tenant_id: Tenant UUID
            batch_size: Batch size for processing products
        
        Returns:
            Sync result with statistics
        """
        try:
            # Verify tenant exists
            tenant_config = await self.tenant_service.get_tenant_config(tenant_id)
            if not tenant_config:
                raise TenantNotFoundError(f"Tenant not found: {tenant_id}")
            
            logger.info(f"Starting knowledge sync for tenant: {tenant_id}")
            
            # Trigger sync
            result = await self.sync_service.sync_tenant_products(
                tenant_id=tenant_id,
                batch_size=batch_size,
            )
            
            return {
                "success": True,
                "data": {
                    "tenant_id": result.tenant_id,
                    "products_synced": result.products_synced,
                    "products_failed": result.products_failed,
                    "duration_seconds": result.duration_seconds,
                    "status": result.status,
                    "error_message": result.error_message,
                }
            }
            
        except TenantNotFoundError as e:
            logger.warning(f"Tenant not found: {e}")
            return {
                "success": False,
                "error": "TENANT_NOT_FOUND",
                "message": str(e),
                "status_code": 404,
            }
        except Exception as e:
            logger.error(
                f"Failed to sync knowledge for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            return {
                "success": False,
                "error": "SYNC_FAILED",
                "message": str(e),
                "status_code": 500,
            }
    
    async def get_sync_status(self, tenant_id: str) -> Dict[str, Any]:
        """
        GET /admin/tenants/{tenant_id}/knowledge/status
        
        Get current sync status for tenant.
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            Sync status information
        """
        try:
            # Verify tenant exists
            tenant_config = await self.tenant_service.get_tenant_config(tenant_id)
            if not tenant_config:
                raise TenantNotFoundError(f"Tenant not found: {tenant_id}")
            
            # Get sync status
            status = await self.sync_service.get_sync_status(tenant_id)
            
            if not status:
                # No sync status yet (never synced)
                return {
                    "success": True,
                    "data": {
                        "tenant_id": tenant_id,
                        "last_sync_at": None,
                        "product_count": 0,
                        "sync_status": "never_synced",
                        "error_message": None,
                    }
                }
            
            return {
                "success": True,
                "data": {
                    "tenant_id": status.tenant_id,
                    "last_sync_at": status.last_sync_at.isoformat() if status.last_sync_at else None,
                    "product_count": status.product_count,
                    "sync_status": status.sync_status,
                    "error_message": status.error_message,
                }
            }
            
        except TenantNotFoundError as e:
            logger.warning(f"Tenant not found: {e}")
            return {
                "success": False,
                "error": "TENANT_NOT_FOUND",
                "message": str(e),
                "status_code": 404,
            }
        except Exception as e:
            logger.error(
                f"Failed to get sync status for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            return {
                "success": False,
                "error": "QUERY_FAILED",
                "message": str(e),
                "status_code": 500,
            }
    
    async def delete_knowledge(self, tenant_id: str) -> Dict[str, Any]:
        """
        DELETE /admin/tenants/{tenant_id}/knowledge
        
        Delete all knowledge base data for tenant.
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            Deletion result
        """
        try:
            # Verify tenant exists
            tenant_config = await self.tenant_service.get_tenant_config(tenant_id)
            if not tenant_config:
                raise TenantNotFoundError(f"Tenant not found: {tenant_id}")
            
            logger.warning(f"Deleting knowledge base for tenant: {tenant_id}")
            
            # Delete from vector store
            from ..infrastructure.vector_store import get_vector_store
            vector_store = get_vector_store()
            
            deleted = await vector_store.delete_collection(tenant_id)
            
            # Delete from knowledge_products table
            query = """
            DELETE FROM knowledge_products
            WHERE tenant_id = $1
            """
            await self.db.execute(query, tenant_id)
            
            # Delete sync status
            delete_status_query = """
            DELETE FROM knowledge_sync_status
            WHERE tenant_id = $1
            """
            await self.db.execute(delete_status_query, tenant_id)
            
            logger.info(f"Deleted knowledge base for tenant: {tenant_id}")
            
            return {
                "success": True,
                "data": {
                    "tenant_id": tenant_id,
                    "collection_deleted": deleted,
                    "message": "Knowledge base deleted successfully",
                }
            }
            
        except TenantNotFoundError as e:
            logger.warning(f"Tenant not found: {e}")
            return {
                "success": False,
                "error": "TENANT_NOT_FOUND",
                "message": str(e),
                "status_code": 404,
            }
        except Exception as e:
            logger.error(
                f"Failed to delete knowledge for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            return {
                "success": False,
                "error": "DELETE_FAILED",
                "message": str(e),
                "status_code": 500,
            }

