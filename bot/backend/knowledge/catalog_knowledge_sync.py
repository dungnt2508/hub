"""
Catalog Knowledge Sync Service - Sync products from catalog to vector store
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

from ..infrastructure.catalog_client import CatalogClient, CatalogProduct
from ..infrastructure.vector_store import get_vector_store, VectorPoint
from ..infrastructure.ai_provider import AIProvider
from ..shared.logger import logger
from ..shared.exceptions import ExternalServiceError
from .product_text_builder import build_product_text, build_product_metadata


@dataclass
class SyncResult:
    """Sync operation result"""
    tenant_id: str
    products_synced: int
    products_failed: int
    duration_seconds: float
    status: str  # 'completed', 'failed', 'partial'
    error_message: Optional[str] = None


@dataclass
class SyncStatus:
    """Current sync status for tenant"""
    tenant_id: str
    last_sync_at: Optional[datetime]
    product_count: int
    sync_status: str  # 'syncing', 'completed', 'failed'
    error_message: Optional[str] = None


class CatalogKnowledgeSyncService:
    """
    Service to sync products from catalog service to vector store.
    
    Responsibilities:
    - Fetch products from catalog API
    - Generate embeddings
    - Store in vector DB
    - Track sync status
    """
    
    def __init__(
        self,
        db_connection,
        catalog_client: Optional[CatalogClient] = None,
        ai_provider: Optional[AIProvider] = None,
    ):
        """
        Initialize sync service.
        
        Args:
            db_connection: PostgreSQL connection pool
            catalog_client: Optional CatalogClient instance
            ai_provider: Optional AIProvider instance
        """
        self.db = db_connection
        self.catalog_client = catalog_client or CatalogClient()
        self.ai_provider = ai_provider or AIProvider()
        self.vector_store = get_vector_store()
        logger.info("CatalogKnowledgeSyncService initialized")
    
    async def sync_tenant_products(
        self,
        tenant_id: str,
        batch_size: int = 10,
    ) -> SyncResult:
        """
        Sync all products for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            batch_size: Number of products to process in parallel
        
        Returns:
            SyncResult with sync statistics
        """
        start_time = datetime.now()
        
        try:
            # Update sync status to 'syncing'
            await self._update_sync_status(
                tenant_id,
                sync_status="syncing",
                error_message=None,
            )
            
            # Fetch all products from catalog (Priority 2: filter by tenant_id)
            logger.info(f"Fetching products for tenant {tenant_id}")
            products = await self.catalog_client.get_all_products(
                tenant_id=tenant_id,  # Priority 2: Pass tenant_id to filter products
                status="published",
                review_status="approved",
            )
            
            if not products:
                logger.warning(f"No products found for tenant {tenant_id}")
                await self._update_sync_status(
                    tenant_id,
                    sync_status="completed",
                    product_count=0,
                )
                return SyncResult(
                    tenant_id=tenant_id,
                    products_synced=0,
                    products_failed=0,
                    duration_seconds=0.0,
                    status="completed",
                )
            
            # Ensure collection exists
            await self.vector_store.create_collection(tenant_id)
            
            # Process products in batches
            products_synced = 0
            products_failed = 0
            
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                
                # Sync batch
                batch_synced, batch_failed = await self._sync_product_batch(
                    tenant_id,
                    batch,
                )
                
                products_synced += batch_synced
                products_failed += batch_failed
                
                logger.info(
                    f"Synced batch {i // batch_size + 1}: "
                    f"{batch_synced} succeeded, {batch_failed} failed"
                )
            
            # Update sync status
            duration = (datetime.now() - start_time).total_seconds()
            status = "completed" if products_failed == 0 else "partial"
            
            await self._update_sync_status(
                tenant_id,
                sync_status=status,
                product_count=products_synced,
                last_sync_at=datetime.now(),
            )
            
            logger.info(
                f"Sync completed for tenant {tenant_id}: "
                f"{products_synced} products synced, {products_failed} failed, "
                f"duration: {duration:.2f}s"
            )
            
            return SyncResult(
                tenant_id=tenant_id,
                products_synced=products_synced,
                products_failed=products_failed,
                duration_seconds=duration,
                status=status,
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            logger.error(
                f"Sync failed for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            
            await self._update_sync_status(
                tenant_id,
                sync_status="failed",
                error_message=error_msg,
            )
            
            return SyncResult(
                tenant_id=tenant_id,
                products_synced=0,
                products_failed=0,
                duration_seconds=duration,
                status="failed",
                error_message=error_msg,
            )
    
    async def _sync_product_batch(
        self,
        tenant_id: str,
        products: List[CatalogProduct],
    ) -> tuple[int, int]:
        """
        Sync a batch of products.
        
        Args:
            tenant_id: Tenant UUID
            products: List of products to sync
        
        Returns:
            Tuple of (synced_count, failed_count)
        """
        synced = 0
        failed = 0
        
        # Prepare vectors
        vectors = []
        for product in products:
            try:
                # Build text representation
                product_text = build_product_text(product)
                
                # Generate embedding
                embedding = await self.ai_provider.embed(product_text)
                
                # Build metadata
                metadata = build_product_metadata(product)
                
                # Create vector point
                vector_point = VectorPoint(
                    id=product.id,  # Use product ID as vector ID
                    vector=embedding,
                    metadata=metadata,
                )
                vectors.append(vector_point)
                
            except Exception as e:
                logger.warning(
                    f"Failed to prepare product {product.id}: {e}",
                    extra={"product_id": product.id, "tenant_id": tenant_id}
                )
                failed += 1
                continue
        
        # Upsert vectors
        if vectors:
            try:
                await self.vector_store.upsert_vectors(tenant_id, vectors)
                synced += len(vectors)
                
                # Update knowledge_products table
                await self._update_knowledge_products(tenant_id, products)
                
            except Exception as e:
                logger.error(
                    f"Failed to upsert vectors: {e}",
                    exc_info=True,
                    extra={"tenant_id": tenant_id, "vector_count": len(vectors)}
                )
                failed += len(vectors)
        
        return synced, failed
    
    async def sync_product(
        self,
        tenant_id: str,
        product: CatalogProduct,
    ) -> bool:
        """
        Sync a single product.
        
        Args:
            tenant_id: Tenant UUID
            product: Product to sync
        
        Returns:
            True if successful
        """
        try:
            # Build text and embedding
            product_text = build_product_text(product)
            embedding = await self.ai_provider.embed(product_text)
            
            # Build metadata
            metadata = build_product_metadata(product)
            
            # Create vector point
            vector_point = VectorPoint(
                id=product.id,
                vector=embedding,
                metadata=metadata,
            )
            
            # Upsert
            await self.vector_store.upsert_vectors(tenant_id, [vector_point])
            
            # Update knowledge_products table
            await self._update_knowledge_products(tenant_id, [product])
            
            logger.info(
                f"Synced product {product.id} for tenant {tenant_id}",
                extra={"product_id": product.id, "tenant_id": tenant_id}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to sync product {product.id}: {e}",
                exc_info=True,
                extra={"product_id": product.id, "tenant_id": tenant_id}
            )
            return False
    
    async def delete_product(
        self,
        tenant_id: str,
        product_id: str,
    ) -> bool:
        """
        Delete a product from knowledge base.
        
        Args:
            tenant_id: Tenant UUID
            product_id: Product UUID to delete
        
        Returns:
            True if successful
        """
        try:
            # Delete from vector store
            await self.vector_store.delete_points(tenant_id, [product_id])
            
            # Delete from knowledge_products table
            query = """
            DELETE FROM knowledge_products
            WHERE tenant_id = $1 AND product_id = $2
            """
            await self.db.execute(query, tenant_id, product_id)
            
            logger.info(
                f"Deleted product {product_id} from knowledge base",
                extra={"product_id": product_id, "tenant_id": tenant_id}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to delete product {product_id}: {e}",
                exc_info=True,
                extra={"product_id": product_id, "tenant_id": tenant_id}
            )
            return False
    
    async def get_sync_status(self, tenant_id: str) -> Optional[SyncStatus]:
        """
        Get current sync status for tenant.
        
        Args:
            tenant_id: Tenant UUID
        
        Returns:
            SyncStatus or None if not found
        """
        try:
            query = """
            SELECT last_sync_at, product_count, sync_status, error_message
            FROM knowledge_sync_status
            WHERE tenant_id = $1
            """
            row = await self.db.fetchrow(query, tenant_id)
            
            if not row:
                return None
            
            return SyncStatus(
                tenant_id=tenant_id,
                last_sync_at=row['last_sync_at'],
                product_count=row['product_count'] or 0,
                sync_status=row['sync_status'] or 'unknown',
                error_message=row['error_message'],
            )
            
        except Exception as e:
            logger.error(
                f"Failed to get sync status for tenant {tenant_id}: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
            return None
    
    async def _update_sync_status(
        self,
        tenant_id: str,
        sync_status: str,
        product_count: Optional[int] = None,
        last_sync_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ):
        """Update sync status in database"""
        try:
            query = """
            INSERT INTO knowledge_sync_status (
                tenant_id, sync_status, product_count, last_sync_at, error_message, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW())
            ON CONFLICT (tenant_id) DO UPDATE SET
                sync_status = EXCLUDED.sync_status,
                product_count = COALESCE(EXCLUDED.product_count, knowledge_sync_status.product_count),
                last_sync_at = COALESCE(EXCLUDED.last_sync_at, knowledge_sync_status.last_sync_at),
                error_message = EXCLUDED.error_message,
                updated_at = NOW()
            """
            
            await self.db.execute(
                query,
                tenant_id,
                sync_status,
                product_count,
                last_sync_at,
                error_message,
            )
            
        except Exception as e:
            logger.error(
                f"Failed to update sync status: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )
    
    async def _update_knowledge_products(
        self,
        tenant_id: str,
        products: List[CatalogProduct],
    ):
        """Update knowledge_products table"""
        try:
            for product in products:
                query = """
                INSERT INTO knowledge_products (
                    id, tenant_id, product_id, vector_id, title, description, synced_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (tenant_id, product_id) DO UPDATE SET
                    vector_id = EXCLUDED.vector_id,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    synced_at = NOW()
                """
                
                await self.db.execute(
                    query,
                    str(uuid.uuid4()),  # knowledge_products.id
                    tenant_id,
                    product.id,
                    product.id,  # vector_id (same as product_id)
                    product.title[:500],  # Truncate if too long
                    product.description[:5000] if product.description else None,
                )
                
        except Exception as e:
            logger.error(
                f"Failed to update knowledge_products: {e}",
                exc_info=True,
                extra={"tenant_id": tenant_id}
            )

