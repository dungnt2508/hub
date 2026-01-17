"""Catalog domain objects"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class Product:
    """Product domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        sku: str,
        slug: str,
        name: str,
        category: Optional[str],
        status: str,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.sku = sku
        self.slug = slug
        self.name = name
        self.category = category
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at


class ProductAttribute:
    """Product attribute domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        product_id: UUID,
        attributes_key: str,
        attributes_value: str,
        attributes_value_type: str,
        created_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.product_id = product_id
        self.attributes_key = attributes_key
        self.attributes_value = attributes_value
        self.attributes_value_type = attributes_value_type
        self.created_at = created_at


class UseCase:
    """Use case domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        product_id: UUID,
        type: str,
        description: str,
        created_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.product_id = product_id
        self.type = type  # allowed, disallowed
        self.description = description
        self.created_at = created_at


class FAQ:
    """FAQ domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        scope: str,
        product_id: Optional[UUID],
        question: str,
        answer: str,
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.scope = scope  # global, product
        self.product_id = product_id
        self.question = question
        self.answer = answer
        self.created_at = created_at
        self.updated_at = updated_at


class Comparison:
    """Comparison domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        product_a: UUID,
        product_b: UUID,
        allowed_attributes: Optional[List[str]],
        created_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.product_a = product_a
        self.product_b = product_b
        self.allowed_attributes = allowed_attributes or []
        self.created_at = created_at


class Guardrail:
    """Guardrail domain object"""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        forbidden_topics: Optional[List[str]],
        disclaimers: Optional[List[str]],
        fallback_message: Optional[str],
        created_at: datetime,
        updated_at: datetime
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.forbidden_topics = forbidden_topics or []
        self.disclaimers = disclaimers or []
        self.fallback_message = fallback_message
        self.created_at = created_at
        self.updated_at = updated_at
