"""
Product Text Builder - Build searchable text representation from product data
"""
from typing import List

from ..infrastructure.catalog_client import CatalogProduct


def build_product_text(product: CatalogProduct) -> str:
    """
    Build searchable text representation from product data.
    
    This text will be used for embedding generation and semantic search.
    
    Args:
        product: CatalogProduct instance
    
    Returns:
        Formatted text string
    """
    parts = []
    
    # Title (most important)
    if product.title:
        parts.append(f"Title: {product.title}")
    
    # Description
    if product.description:
        parts.append(f"Description: {product.description}")
    
    # Long description (if available)
    if product.long_description:
        parts.append(f"Details: {product.long_description}")
    
    # Type
    if product.type:
        parts.append(f"Type: {product.type}")
    
    # Tags
    if product.tags:
        tags_str = ", ".join(product.tags)
        parts.append(f"Tags: {tags_str}")
    
    # Features
    if product.features:
        features_str = ", ".join(product.features)
        parts.append(f"Features: {features_str}")
    
    # Requirements (can be useful for matching)
    if product.requirements:
        requirements_str = ", ".join(product.requirements)
        parts.append(f"Requirements: {requirements_str}")
    
    # Pricing info (for filtering context)
    if product.is_free:
        parts.append("Pricing: Free")
    elif product.price:
        parts.append(f"Pricing: {product.price} VND")
    
    # Join all parts
    text = "\n".join(parts)
    
    return text


def build_product_metadata(product: CatalogProduct) -> dict:
    """
    Build metadata dictionary for vector store.
    
    Args:
        product: CatalogProduct instance
    
    Returns:
        Metadata dictionary
    """
    return {
        "product_id": product.id,
        "seller_id": product.seller_id,
        "title": product.title,
        "type": product.type,
        "tags": product.tags,
        "is_free": product.is_free,
        "price": product.price,
        "status": product.status,
        "review_status": product.review_status,
        "downloads": product.downloads,
        "rating": product.rating,
        "reviews_count": product.reviews_count,
        "version": product.version,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }

