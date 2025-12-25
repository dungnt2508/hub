"""
Catalog Webhook Handler - Receive product update events from catalog service
"""
from typing import Dict, Any, Optional

from ...knowledge.catalog_knowledge_sync import CatalogKnowledgeSyncService
from ...infrastructure.catalog_client import CatalogClient, CatalogProduct
from ...shared.logger import logger
from ...shared.exceptions import TenantNotFoundError, InvalidInputError


class CatalogWebhookHandler:
    """
    Webhook handler for catalog service product updates.
    
    Events:
    - product.created → Sync product
    - product.updated → Re-sync product
    - product.deleted → Delete from vector store
    """
    
    def __init__(self, db_connection):
        """
        Initialize webhook handler.
        
        Args:
            db_connection: PostgreSQL connection pool
        """
        self.db = db_connection
        self.sync_service = CatalogKnowledgeSyncService(db_connection)
        self.catalog_client = CatalogClient()
        logger.info("CatalogWebhookHandler initialized")
    
    async def handle_product_event(
        self,
        tenant_id: str,
        event: str,
        product_id: str,
    ) -> Dict[str, Any]:
        """
        Handle product update event from catalog service.
        
        Args:
            tenant_id: Tenant UUID
            event: Event type ('created', 'updated', 'deleted')
            product_id: Product UUID
        
        Returns:
            Processing result
        """
        try:
            logger.info(
                f"Handling product event: {event} for product {product_id}",
                extra={
                    "tenant_id": tenant_id,
                    "event": event,
                    "product_id": product_id,
                }
            )
            
            if event == "deleted":
                # Delete product from knowledge base
                deleted = await self.sync_service.delete_product(tenant_id, product_id)
                
                return {
                    "success": deleted,
                    "event": event,
                    "product_id": product_id,
                    "message": "Product deleted from knowledge base" if deleted else "Failed to delete product",
                }
            
            elif event in ["created", "updated"]:
                # Fetch product from catalog and sync
                # Task 4.2: Pass tenant_id to get_product (required)
                product = await self.catalog_client.get_product(product_id, tenant_id=tenant_id)
                
                if not product:
                    logger.warning(
                        f"Product not found in catalog: {product_id}",
                        extra={"tenant_id": tenant_id, "product_id": product_id}
                    )
                    return {
                        "success": False,
                        "event": event,
                        "product_id": product_id,
                        "message": "Product not found in catalog",
                    }
                
                # Only sync if product is published and approved
                if product.status != "published" or product.review_status != "approved":
                    logger.info(
                        f"Product {product_id} is not published/approved, skipping sync",
                        extra={
                            "tenant_id": tenant_id,
                            "product_id": product_id,
                            "status": product.status,
                            "review_status": product.review_status,
                        }
                    )
                    return {
                        "success": True,
                        "event": event,
                        "product_id": product_id,
                        "message": "Product skipped (not published/approved)",
                    }
                
                # Sync product
                synced = await self.sync_service.sync_product(tenant_id, product)
                
                return {
                    "success": synced,
                    "event": event,
                    "product_id": product_id,
                    "message": "Product synced successfully" if synced else "Failed to sync product",
                }
            
            else:
                logger.warning(
                    f"Unknown event type: {event}",
                    extra={"tenant_id": tenant_id, "event": event}
                )
                return {
                    "success": False,
                    "event": event,
                    "product_id": product_id,
                    "message": f"Unknown event type: {event}",
                }
                
        except Exception as e:
            logger.error(
                f"Failed to handle product event: {e}",
                exc_info=True,
                extra={
                    "tenant_id": tenant_id,
                    "event": event,
                    "product_id": product_id,
                }
            )
            return {
                "success": False,
                "event": event,
                "product_id": product_id,
                "message": str(e),
                "error": "PROCESSING_FAILED",
            }

