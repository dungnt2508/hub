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
    listing_status: Literal["published", "draft", "archived"] = "draft"
    stock_status: Literal["in_stock", "out_of_stock", "unknown"] = "unknown"
    quantity: Optional[int] = None
    
    def __post_init__(self):
        """Validate invariants"""
        # Validate quantity
        if self.quantity is not None:
            if not isinstance(self.quantity, int):
                raise ValueError(f"Quantity must be an integer or None, got: {type(self.quantity)}")
            if self.quantity < 0:
                raise ValueError("Quantity cannot be negative")
        
        # Validate listing_status
        if not isinstance(self.listing_status, str):
            raise ValueError(f"listing_status must be a string, got: {type(self.listing_status)}")
        
        valid_listing_statuses = ["published", "draft", "archived"]
        if self.listing_status not in valid_listing_statuses:
            raise ValueError(f"Invalid listing_status: {self.listing_status}. Valid: {valid_listing_statuses}")
        
        # Validate stock_status
        if not isinstance(self.stock_status, str):
            raise ValueError(f"stock_status must be a string, got: {type(self.stock_status)}")
        
        valid_stock_statuses = ["in_stock", "out_of_stock", "unknown"]
        if self.stock_status not in valid_stock_statuses:
            raise ValueError(f"Invalid stock_status: {self.stock_status}. Valid: {valid_stock_statuses}")
    
    def availability_state(self) -> Literal["available", "unavailable", "unknown"]:
        """Determine availability state for customer queries"""
        if self.listing_status == "draft":
            return "unavailable"
        if self.listing_status == "archived":
            return "unavailable"
        if self.stock_status == "unknown":
            return "unknown"
        return "available" if self.stock_status == "in_stock" else "unavailable"
    
    def get_availability_text(self) -> str:
        """Get human-readable availability text"""
        if self.listing_status == "draft":
            return "Chưa được phát hành"
        if self.listing_status == "archived":
            return "Đã ngừng bán"
        if self.stock_status == "unknown":
            return "Không có dữ liệu tồn kho"
        if self.stock_status == "out_of_stock":
            return "Hết hàng"
        if self.quantity is None:
            return "Còn hàng"
        if self.quantity > 0:
            return f"Còn {self.quantity} sản phẩm"
        return "Hết hàng"
    
    def __str__(self) -> str:
        """String representation"""
        return self.get_availability_text()

