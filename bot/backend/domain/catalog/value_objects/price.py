"""
Price Value Object - Immutable price representation
"""
from dataclasses import dataclass
from typing import Literal


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
    amount: float
    currency: str = "VND"
    price_type: Literal["free", "onetime", "subscription"] = "free"
    
    def __post_init__(self):
        """Validate invariants"""
        # Validate amount
        if not isinstance(self.amount, (int, float)):
            raise ValueError(f"Price amount must be a number, got: {type(self.amount)}")
        
        if self.amount < 0:
            raise ValueError("Price amount cannot be negative")
        
        # Validate currency
        if not isinstance(self.currency, str):
            raise ValueError(f"Currency must be a string, got: {type(self.currency)}")
        
        supported_currencies = ["VND", "USD", "EUR"]
        if self.currency not in supported_currencies:
            raise ValueError(f"Unsupported currency: {self.currency}. Supported: {supported_currencies}")
        
        # Validate price_type
        if not isinstance(self.price_type, str):
            raise ValueError(f"Price type must be a string, got: {type(self.price_type)}")
        
        valid_price_types = ["free", "onetime", "subscription"]
        if self.price_type not in valid_price_types:
            raise ValueError(f"Invalid price_type: {self.price_type}. Valid: {valid_price_types}")
    
    def is_free(self) -> bool:
        """Check if product is free"""
        return self.amount == 0 or self.price_type == "free"
    
    def format(self) -> str:
        """Format price for display"""
        if self.is_free():
            return "Miễn phí"
        
        currency_symbols = {
            "VND": "₫",
            "USD": "$",
            "EUR": "€"
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        
        if self.price_type == "subscription":
            return f"{symbol}{self.amount:.2f}/tháng"
        else:
            return f"{symbol}{self.amount:.2f}"
    
    def __str__(self) -> str:
        """String representation"""
        return self.format()

