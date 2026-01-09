"""
Knowledge Sync Scheduler - Scheduled synchronization of knowledge base
Runs periodic syncs of catalog products and HR policies
"""
import asyncio
from typing import Optional
from datetime import datetime, timedelta
import uuid

from ..infrastructure.database_client import DatabaseClient
from ..infrastructure.catalog_client import CatalogClient
from ..infrastructure.ai_provider import AIProvider
from ..shared.config import config
from ..shared.logger import logger
from .catalog_knowledge_sync import CatalogKnowledgeSyncService


class KnowledgeSyncScheduler:
    """
    Scheduler for periodic knowledge synchronization.
    
    Responsibilities:
    - Sync catalog products periodically
    - Sync HR policies periodically
    - Track sync history
    - Handle failures gracefully
    """
    
    def __init__(
        self,
        db_client: Optional[DatabaseClient] = None,
        catalog_client: Optional[CatalogClient] = None,
        ai_provider: Optional[AIProvider] = None,
        sync_interval_hours: int = 24,
    ):
        """
        Initialize scheduler.
        
        Args:
            db_client: Database client
            catalog_client: Catalog client
            ai_provider: AI provider
            sync_interval_hours: Interval between syncs (hours)
        """
        self.db_client = db_client
        self.catalog_client = catalog_client or CatalogClient()
        self.ai_provider = ai_provider or AIProvider()
        self.sync_interval_hours = sync_interval_hours
        self.is_running = False
        self._sync_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"KnowledgeSyncScheduler initialized (interval: {sync_interval_hours}h)"
        )
    
    async def start(self):
        """Start the sync scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting knowledge sync scheduler...")
        
        self._sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop(self):
        """Stop the sync scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping knowledge sync scheduler...")
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
    
    async def _sync_loop(self):
        """Main sync loop"""
        while self.is_running:
            try:
                # Run sync
                await self._run_sync()
                
                # Wait for next sync
                await asyncio.sleep(self.sync_interval_hours * 3600)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Error in sync loop: {e}",
                    exc_info=True
                )
                # Wait before retrying
                await asyncio.sleep(60)
    
    async def _run_sync(self):
        """Run sync for all tenants"""
        try:
            logger.info("Starting scheduled knowledge sync...")
            
            if not self.db_client:
                logger.warning("No database client, skipping sync")
                return
            
            # Get all tenants
            query = "SELECT DISTINCT tenant_id FROM tenants WHERE is_active = true"
            tenants = await self.db_client.fetch(query)
            
            if not tenants:
                logger.info("No active tenants found")
                return
            
            logger.info(f"Syncing knowledge for {len(tenants)} tenants")
            
            # Sync each tenant
            sync_service = CatalogKnowledgeSyncService(
                db_connection=self.db_client,
                catalog_client=self.catalog_client,
                ai_provider=self.ai_provider,
            )
            
            for tenant in tenants:
                tenant_id = tenant['tenant_id']
                
                try:
                    logger.info(f"Syncing catalog products for tenant {tenant_id}")
                    
                    result = await sync_service.sync_tenant_products(
                        tenant_id=tenant_id,
                        batch_size=10,
                    )
                    
                    logger.info(
                        f"Sync completed for tenant {tenant_id}",
                        extra={
                            "status": result.status,
                            "products_synced": result.products_synced,
                            "products_failed": result.products_failed,
                            "duration": result.duration_seconds,
                        }
                    )
                
                except Exception as e:
                    logger.error(
                        f"Sync failed for tenant {tenant_id}: {e}",
                        exc_info=True,
                        extra={"tenant_id": tenant_id}
                    )
        
        except Exception as e:
            logger.error(
                f"Sync loop error: {e}",
                exc_info=True
            )
    
    async def sync_now(self, tenant_id: str) -> dict:
        """
        Trigger an immediate sync for a tenant.
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            Sync result
        """
        try:
            logger.info(f"Triggering immediate sync for tenant {tenant_id}")
            
            if not self.db_client:
                raise ValueError("No database client")
            
            sync_service = CatalogKnowledgeSyncService(
                db_connection=self.db_client,
                catalog_client=self.catalog_client,
                ai_provider=self.ai_provider,
            )
            
            result = await sync_service.sync_tenant_products(
                tenant_id=tenant_id,
                batch_size=10,
            )
            
            return {
                "status": result.status,
                "products_synced": result.products_synced,
                "products_failed": result.products_failed,
                "duration": result.duration_seconds,
                "error": result.error_message,
            }
        
        except Exception as e:
            logger.error(
                f"Failed to trigger sync for tenant {tenant_id}: {e}",
                exc_info=True
            )
            return {
                "status": "failed",
                "error": str(e),
            }


# Global scheduler instance
_scheduler_instance: Optional[KnowledgeSyncScheduler] = None


def get_scheduler() -> KnowledgeSyncScheduler:
    """Get or create global scheduler instance"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = KnowledgeSyncScheduler()
    
    return _scheduler_instance

