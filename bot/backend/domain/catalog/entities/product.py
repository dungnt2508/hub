"""
Product Entity - Aggregate root for catalog domain
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from ..value_objects.price import Price
from ..value_objects.availability import Availability
from ..value_objects.attribute import Attribute


@dataclass
class Product:
    """
    Product aggregate root.
    
    This is the central entity for catalog domain.
    All product-related operations should go through this entity.
    
    Business rules:
    - Product must have title and description
    - If price is None, product is considered free
    - Availability determines if product can be purchased
    """
    id: str
    title: str
    description: str
    price: Optional[Price] = None
    availability: Optional[Availability] = None
    features: List[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize defaults and validate invariants"""
        # Validate title
        if not self.title or not self.title.strip():
            raise ValueError("Product title cannot be empty")
        if len(self.title.strip()) > 500:
            raise ValueError("Product title cannot exceed 500 characters")
        self.title = self.title.strip()
        
        # Validate description
        if not self.description or not self.description.strip():
            raise ValueError("Product description cannot be empty")
        if len(self.description.strip()) > 10000:
            raise ValueError("Product description cannot exceed 10000 characters")
        self.description = self.description.strip()
        
        # Validate ID
        if not self.id or not self.id.strip():
            raise ValueError("Product ID cannot be empty")
        self.id = self.id.strip()
        
        # Initialize defaults
        if self.features is None:
            self.features = []
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        
        # Validate features and tags are lists
        if not isinstance(self.features, list):
            raise ValueError("Product features must be a list")
        if not isinstance(self.tags, list):
            raise ValueError("Product tags must be a list")
        if not isinstance(self.metadata, dict):
            raise ValueError("Product metadata must be a dictionary")
        
        # Validate feature items are strings
        for i, feature in enumerate(self.features):
            if not isinstance(feature, str):
                raise ValueError(f"Product feature at index {i} must be a string")
        
        # Validate tag items are strings
        for i, tag in enumerate(self.tags):
            if not isinstance(tag, str):
                raise ValueError(f"Product tag at index {i} must be a string")
        
        # Default availability if not provided
        if self.availability is None:
            self.availability = Availability(
                in_stock=True,
                status="published"
            )
        
        # Validate price if provided
        if self.price is not None and not isinstance(self.price, Price):
            raise ValueError("Product price must be a Price value object")
    
    def is_available(self) -> bool:
        """Business rule: Check if product is available for purchase"""
        if not self.availability:
            return False
        return self.availability.is_available()
    
    def is_free(self) -> bool:
        """Business rule: Check if product is free"""
        if not self.price:
            return True
        return self.price.is_free()
    
    def has_feature(self, feature: str) -> bool:
        """Business rule: Check if product has specific feature"""
        if not self.features:
            return False
        feature_lower = feature.lower()
        return any(feature_lower in f.lower() for f in self.features)
    
    def has_tag(self, tag: str) -> bool:
        """Business rule: Check if product has specific tag"""
        if not self.tags:
            return False
        tag_lower = tag.lower()
        return any(tag_lower == t.lower() for t in self.tags)
    
    def matches_price_range(self, min_price: Optional[float] = None, max_price: Optional[float] = None) -> bool:
        """Business rule: Check if product price is within range"""
        if not self.price or self.price.is_free():
            # Free products match any range that includes 0
            return min_price is None or min_price <= 0
        
        amount = self.price.amount
        if min_price is not None and amount < min_price:
            return False
        if max_price is not None and amount > max_price:
            return False
        return True
    
    def matches_query(self, query: str) -> bool:
        """Business rule: Check if product matches search query"""
        query_lower = query.lower()
        
        # Check title
        if query_lower in self.title.lower():
            return True
        
        # Check description
        if query_lower in self.description.lower():
            return True
        
        # Check tags
        if any(query_lower in tag.lower() for tag in self.tags):
            return True
        
        # Check features
        if any(query_lower in feature.lower() for feature in self.features):
            return True
        
        return False
    
    def get_price_display(self) -> str:
        """Get formatted price for display"""
        if not self.price:
            return "Miễn phí"
        return self.price.format()
    
    def get_availability_display(self) -> str:
        """Get formatted availability for display"""
        if not self.availability:
            return "Không xác định"
        return self.availability.get_availability_text()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for API response"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price.amount if self.price else None,
            "price_display": self.get_price_display(),
            "currency": self.price.currency if self.price else None,
            "price_type": self.price.price_type if self.price else "free",
            "is_free": self.is_free(),
            "is_available": self.is_available(),
            "availability": self.get_availability_display(),
            "features": self.features,
            "tags": self.tags,
            "metadata": self.metadata,
        }

