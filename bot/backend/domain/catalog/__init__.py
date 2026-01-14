"""
Catalog Domain - Product search and recommendations with Clean Architecture
"""

from .entry_handler import CatalogEntryHandler
from .intent_classifier import CatalogIntentClassifier, CatalogIntentType, ClassificationResult
from .hybrid_search_helper import CatalogHybridSearchHelper

# Domain entities
from .entities.product import Product

# Value objects
from .value_objects.price import Price
from .value_objects.availability import Availability
from .value_objects.attribute import Attribute

# Use cases
from .use_cases import (
    CatalogUseCase,
    SearchProductUseCase,
    GetProductInfoUseCase,
    CompareProductsUseCase,
    CheckAvailabilityUseCase,
    GetProductPriceUseCase,
)

# Ports
from .ports.repository import ICatalogRepository

# Adapters
from .adapters.catalog_repository import CatalogRepositoryAdapter

__all__ = [
    # Entry handler
    "CatalogEntryHandler",
    # Intent classifier
    "CatalogIntentClassifier",
    "CatalogIntentType",
    "ClassificationResult",
    # Hybrid search
    "CatalogHybridSearchHelper",
    # Domain entities
    "Product",
    # Value objects
    "Price",
    "Availability",
    "Attribute",
    # Use cases
    "CatalogUseCase",
    "SearchProductUseCase",
    "GetProductInfoUseCase",
    "CompareProductsUseCase",
    "CheckAvailabilityUseCase",
    "GetProductPriceUseCase",
    # Ports
    "ICatalogRepository",
    # Adapters
    "CatalogRepositoryAdapter",
]

