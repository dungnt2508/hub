"""Catalog repository"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.domain.catalog import (
    Product,
    ProductAttribute,
    UseCase,
    FAQ,
    Comparison,
    Guardrail,
)


class CatalogRepository:
    """Repository for catalog data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # Products
    async def get_product(
        self, 
        product_id: UUID, 
        tenant_id: UUID
    ) -> Optional[Product]:
        """Get product by ID with tenant isolation"""
        stmt = text("""
            SELECT id, tenant_id, sku, slug, name, category, status, created_at, updated_at
            FROM products
            WHERE id = :product_id AND tenant_id = :tenant_id
        """)
        result = await self.session.execute(
            stmt, 
            {"product_id": product_id, "tenant_id": tenant_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return Product(
            id=row[0],
            tenant_id=row[1],
            sku=row[2],
            slug=row[3],
            name=row[4],
            category=row[5],
            status=row[6],
            created_at=row[7],
            updated_at=row[8],
        )
    
    async def get_product_by_sku(
        self, 
        sku: str, 
        tenant_id: UUID
    ) -> Optional[Product]:
        """Get product by SKU"""
        stmt = text("""
            SELECT id, tenant_id, sku, slug, name, category, status, created_at, updated_at
            FROM products
            WHERE sku = :sku AND tenant_id = :tenant_id
        """)
        result = await self.session.execute(
            stmt, 
            {"sku": sku, "tenant_id": tenant_id}
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return Product(
            id=row[0],
            tenant_id=row[1],
            sku=row[2],
            slug=row[3],
            name=row[4],
            category=row[5],
            status=row[6],
            created_at=row[7],
            updated_at=row[8],
        )
    
    async def search_products(
        self,
        tenant_id: UUID,
        query: Optional[str] = None,
        category: Optional[str] = None,
        status: str = "active",
        limit: int = 50,
        offset: int = 0
    ) -> List[Product]:
        """Search products"""
        conditions = ["tenant_id = :tenant_id", "status = :status"]
        params = {"tenant_id": tenant_id, "status": status, "limit": limit, "offset": offset}
        
        if query:
            conditions.append("(name ILIKE :query OR sku ILIKE :query)")
            params["query"] = f"%{query}%"
        
        if category:
            conditions.append("category = :category")
            params["category"] = category
        
        where_clause = " AND ".join(conditions)
        
        stmt = text(f"""
            SELECT id, tenant_id, sku, slug, name, category, status, created_at, updated_at
            FROM products
            WHERE {where_clause}
            ORDER BY name ASC
            LIMIT :limit OFFSET :offset
        """)
        result = await self.session.execute(stmt, params)
        rows = result.fetchall()
        
        return [
            Product(
                id=row[0],
                tenant_id=row[1],
                sku=row[2],
                slug=row[3],
                name=row[4],
                category=row[5],
                status=row[6],
                created_at=row[7],
                updated_at=row[8],
            )
            for row in rows
        ]
    
    # Product Attributes
    async def get_product_attributes(
        self,
        product_id: UUID,
        tenant_id: UUID
    ) -> List[ProductAttribute]:
        """Get all attributes for a product"""
        stmt = text("""
            SELECT id, tenant_id, product_id, attributes_key, attributes_value, 
                   attributes_value_type, created_at
            FROM product_attributes
            WHERE product_id = :product_id AND tenant_id = :tenant_id
            ORDER BY attributes_key ASC
        """)
        result = await self.session.execute(
            stmt,
            {"product_id": product_id, "tenant_id": tenant_id}
        )
        rows = result.fetchall()
        
        return [
            ProductAttribute(
                id=row[0],
                tenant_id=row[1],
                product_id=row[2],
                attributes_key=row[3],
                attributes_value=row[4],
                attributes_value_type=row[5],
                created_at=row[6],
            )
            for row in rows
        ]
    
    # Use Cases
    async def get_use_cases(
        self,
        product_id: UUID,
        tenant_id: UUID,
        type: Optional[str] = None
    ) -> List[UseCase]:
        """Get use cases for a product"""
        conditions = ["product_id = :product_id", "tenant_id = :tenant_id"]
        params = {"product_id": product_id, "tenant_id": tenant_id}
        
        if type:
            conditions.append("type = :type")
            params["type"] = type
        
        where_clause = " AND ".join(conditions)
        
        stmt = text(f"""
            SELECT id, tenant_id, product_id, type, description, created_at
            FROM use_cases
            WHERE {where_clause}
            ORDER BY type ASC, created_at ASC
        """)
        result = await self.session.execute(stmt, params)
        rows = result.fetchall()
        
        return [
            UseCase(
                id=row[0],
                tenant_id=row[1],
                product_id=row[2],
                type=row[3],
                description=row[4],
                created_at=row[5],
            )
            for row in rows
        ]
    
    # FAQs
    async def get_faqs(
        self,
        tenant_id: UUID,
        product_id: Optional[UUID] = None,
        scope: Optional[str] = None
    ) -> List[FAQ]:
        """Get FAQs"""
        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id}
        
        if product_id:
            conditions.append("product_id = :product_id")
            params["product_id"] = product_id
        
        if scope:
            conditions.append("scope = :scope")
            params["scope"] = scope
        
        where_clause = " AND ".join(conditions)
        
        stmt = text(f"""
            SELECT id, tenant_id, scope, product_id, question, answer, created_at, updated_at
            FROM faqs
            WHERE {where_clause}
            ORDER BY scope DESC, created_at ASC
        """)
        result = await self.session.execute(stmt, params)
        rows = result.fetchall()
        
        return [
            FAQ(
                id=row[0],
                tenant_id=row[1],
                scope=row[2],
                product_id=row[3],
                question=row[4],
                answer=row[5],
                created_at=row[6],
                updated_at=row[7],
            )
            for row in rows
        ]
    
    # Comparisons
    async def get_comparison(
        self,
        product_a: UUID,
        product_b: UUID,
        tenant_id: UUID
    ) -> Optional[Comparison]:
        """Get comparison between two products"""
        stmt = text("""
            SELECT id, tenant_id, product_a, product_b, allowed_attributes, created_at
            FROM comparisons
            WHERE tenant_id = :tenant_id
              AND ((product_a = :product_a AND product_b = :product_b)
                   OR (product_a = :product_b AND product_b = :product_a))
            LIMIT 1
        """)
        result = await self.session.execute(
            stmt,
            {
                "tenant_id": tenant_id,
                "product_a": product_a,
                "product_b": product_b,
            }
        )
        row = result.fetchone()
        
        if not row:
            return None
        
        return Comparison(
            id=row[0],
            tenant_id=row[1],
            product_a=row[2],
            product_b=row[3],
            allowed_attributes=row[4],
            created_at=row[5],
        )
    
    # Guardrails
    async def get_guardrail(
        self,
        tenant_id: UUID
    ) -> Optional[Guardrail]:
        """Get guardrail for tenant"""
        stmt = text("""
            SELECT id, tenant_id, forbidden_topics, disclaimers, fallback_message, 
                   created_at, updated_at
            FROM guardrails
            WHERE tenant_id = :tenant_id
            LIMIT 1
        """)
        result = await self.session.execute(stmt, {"tenant_id": tenant_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return Guardrail(
            id=row[0],
            tenant_id=row[1],
            forbidden_topics=row[2],
            disclaimers=row[3],
            fallback_message=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
