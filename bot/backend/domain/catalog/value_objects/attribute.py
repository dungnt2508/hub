"""
Attribute Value Object - Product attribute representation
"""
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class Attribute:
    """
    Attribute value object (immutable).
    
    Represents a product attribute (feature, tag, metadata, etc.)
    """
    name: str
    value: Any
    attribute_type: Literal["feature", "tag", "metadata", "requirement", "other"] = "other"
    
    def __post_init__(self):
        """Validate invariants"""
        if not self.name or not self.name.strip():
            raise ValueError("Attribute name cannot be empty")
    
    def matches(self, search_term: str) -> bool:
        """Check if attribute matches search term (case-insensitive)"""
        search_lower = search_term.lower()
        name_match = search_lower in self.name.lower()
        value_match = False
        
        if isinstance(self.value, str):
            value_match = search_lower in self.value.lower()
        elif isinstance(self.value, list):
            value_match = any(search_lower in str(v).lower() for v in self.value)
        else:
            value_match = search_lower in str(self.value).lower()
        
        return name_match or value_match
    
    def __str__(self) -> str:
        """String representation"""
        if isinstance(self.value, list):
            return f"{self.name}: {', '.join(str(v) for v in self.value)}"
        return f"{self.name}: {self.value}"

