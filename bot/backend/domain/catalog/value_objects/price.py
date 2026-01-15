"""
Price Value Object - Immutable price representation
"""
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class Price:
    """
    Price value object (immutable).
    
    Represents product pricing information.
    Business rules:
    - Amount cannot be negative
    - Currency must be supported
    - Price type must be valid
    """
    amount: Optional[float]
    currency: Optional[str] = None
    price_type: Literal["free", "onetime", "subscription", "unknown"] = "unknown"
    
    def __post_init__(self):
        """Validate invariants"""
        # Validate amount
        if self.amount is not None and not isinstance(self.amount, (int, float)):
            raise ValueError(f"Price amount must be a number, got: {type(self.amount)}")
        
        if self.amount is not None and self.amount < 0:
            raise ValueError("Price amount cannot be negative")
        
        # Validate currency
        if self.currency is not None:
            if not isinstance(self.currency, str):
                raise ValueError(f"Currency must be a string, got: {type(self.currency)}")
            
            supported_currencies = ["VND", "USD", "EUR"]
            if self.currency not in supported_currencies:
                raise ValueError(f"Unsupported currency: {self.currency}. Supported: {supported_currencies}")
        
        # Validate price_type
        if not isinstance(self.price_type, str):
            raise ValueError(f"Price type must be a string, got: {type(self.price_type)}")
        
        valid_price_types = ["free", "onetime", "subscription", "unknown"]
        if self.price_type not in valid_price_types:
            raise ValueError(f"Invalid price_type: {self.price_type}. Valid: {valid_price_types}")
        
        if self.price_type == "unknown" and self.amount is not None:
            raise ValueError("Price amount must be None when price_type is unknown")
    
    def is_free(self) -> bool:
        """Check if product is free"""
        return self.price_type == "free" or (self.amount == 0 and self.price_type != "unknown")
    
    def is_known(self) -> bool:
        """Check if price data is known"""
        return self.price_type != "unknown"
    
    def format(self) -> str:
        """Format price for display"""
        if not self.is_known():
            return "Chưa có dữ liệu giá"
        if self.is_free():
            return "Miễn phí"
        
        if self.amount is None:
            return "Chưa có dữ liệu giá"
        
        currency_symbols = {
            "VND": "₫",
            "USD": "$",
            "EUR": "€"
        }
        symbol = currency_symbols.get(self.currency or "", self.currency or "")
        
        if self.price_type == "subscription":
            return f"{symbol}{self.amount:.2f}/tháng"
        else:
            return f"{symbol}{self.amount:.2f}"
    
    def __str__(self) -> str:
        """String representation"""
        return self.format()

