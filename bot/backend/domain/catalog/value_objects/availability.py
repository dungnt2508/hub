"""
Availability Value Object - Product availability information
"""
from dataclasses import dataclass
from typing import Optional, Literal


@dataclass(frozen=True)
class Availability:
    """
    Availability value object (immutable).
    
    Represents product availability status.
    Business rules:
    - If in_stock is True, quantity should be > 0 (or None if not tracked)
    - Status must be valid
    """
    in_stock: bool
    quantity: Optional[int] = None
    status: Literal["published", "draft", "archived"] = "published"
    
    def __post_init__(self):
        """Validate invariants"""
        # Validate in_stock is boolean
        if not isinstance(self.in_stock, bool):
            raise ValueError(f"in_stock must be a boolean, got: {type(self.in_stock)}")
        
        # Validate quantity
        if self.quantity is not None:
            if not isinstance(self.quantity, int):
                raise ValueError(f"Quantity must be an integer or None, got: {type(self.quantity)}")
            if self.quantity < 0:
                raise ValueError("Quantity cannot be negative")
            if self.in_stock and self.quantity == 0:
                # Warning: in_stock=True but quantity=0 is inconsistent
                # Allow it but log warning (some systems track availability separately)
                pass
        
        # Validate status
        if not isinstance(self.status, str):
            raise ValueError(f"Status must be a string, got: {type(self.status)}")
        
        valid_statuses = ["published", "draft", "archived"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Valid: {valid_statuses}")
    
    def is_available(self) -> bool:
        """Check if product is available for purchase"""
        return self.in_stock and self.status == "published"
    
    def get_availability_text(self) -> str:
        """Get human-readable availability text"""
        if not self.is_available():
            if self.status == "draft":
                return "Chưa được phát hành"
            elif self.status == "archived":
                return "Đã ngừng bán"
            else:
                return "Hết hàng"
        
        if self.quantity is None:
            return "Còn hàng"
        elif self.quantity > 0:
            return f"Còn {self.quantity} sản phẩm"
        else:
            return "Hết hàng"
    
    def __str__(self) -> str:
        """String representation"""
        return self.get_availability_text()

