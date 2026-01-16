"""
Slot Validator - Validates slot formats at router level

This implements F4.1: Add Slot Validation At Router Level.
Validates slot format (date, number, etc.) before passing to domain.
"""
import re
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dateutil import parser

from ..shared.logger import logger
from ..shared.exceptions import InvalidInputError


class SlotValidator:
    """
    Validates slot formats at router level.
    
    This is basic format validation only - business logic validation
    is still done at domain level.
    """
    
    def __init__(self):
        """Initialize slot validator"""
        # Date patterns
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO format: 2025-01-16
            r'\d{2}/\d{2}/\d{4}',  # US format: 01/16/2025
            r'\d{2}-\d{2}-\d{4}',  # EU format: 16-01-2025
        ]
        
        # Number patterns
        self.number_pattern = r'^-?\d+(\.\d+)?$'
    
    def validate_slots(
        self,
        slots: Dict[str, Any],
        slot_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Validate slot formats.
        
        Args:
            slots: Slots to validate
            slot_types: Optional dict mapping slot_name -> type (date, number, string, etc.)
            
        Returns:
            Validated slots dict (may have converted values)
            
        Raises:
            InvalidInputError: If slot format is invalid
        """
        if not slots:
            return {}
        
        validated = {}
        errors = []
        
        for slot_name, slot_value in slots.items():
            if slot_value is None:
                continue
            
            # Determine slot type
            slot_type = self._infer_slot_type(slot_name, slot_types)
            
            try:
                validated_value = self._validate_slot_value(slot_name, slot_value, slot_type)
                validated[slot_name] = validated_value
            except InvalidInputError as e:
                errors.append(f"{slot_name}: {str(e)}")
                logger.warning(
                    f"Invalid slot format: {slot_name}={slot_value}",
                    extra={"slot_name": slot_name, "slot_value": str(slot_value)[:100]}
                )
        
        if errors:
            raise InvalidInputError(f"Invalid slot formats: {', '.join(errors)}")
        
        return validated
    
    def _infer_slot_type(self, slot_name: str, slot_types: Optional[Dict[str, str]]) -> str:
        """
        Infer slot type from name or explicit types.
        
        Args:
            slot_name: Slot name
            slot_types: Optional explicit slot types
            
        Returns:
            Inferred slot type
        """
        if slot_types and slot_name in slot_types:
            return slot_types[slot_name]
        
        # Infer from slot name
        slot_lower = slot_name.lower()
        
        if any(keyword in slot_lower for keyword in ["date", "ngày", "time", "thời"]):
            return "date"
        elif any(keyword in slot_lower for keyword in ["number", "số", "count", "số lượng", "amount", "số tiền", "id"]):
            return "number"
        elif any(keyword in slot_lower for keyword in ["email", "mail"]):
            return "email"
        elif any(keyword in slot_lower for keyword in ["phone", "điện thoại", "sdt"]):
            return "phone"
        else:
            return "string"
    
    def _validate_slot_value(
        self,
        slot_name: str,
        slot_value: Any,
        slot_type: str
    ) -> Any:
        """
        Validate and convert slot value based on type.
        
        Args:
            slot_name: Slot name
            slot_value: Slot value to validate
            slot_type: Expected slot type
            
        Returns:
            Validated/converted value
            
        Raises:
            InvalidInputError: If validation fails
        """
        if slot_type == "date":
            return self._validate_date(slot_name, slot_value)
        elif slot_type == "number":
            return self._validate_number(slot_name, slot_value)
        elif slot_type == "email":
            return self._validate_email(slot_name, slot_value)
        elif slot_type == "phone":
            return self._validate_phone(slot_name, slot_value)
        else:
            # String - just ensure it's a string
            return str(slot_value) if slot_value is not None else None
    
    def _validate_date(self, slot_name: str, value: Any) -> str:
        """
        Validate date slot.
        
        Args:
            slot_name: Slot name
            value: Date value (string or date object)
            
        Returns:
            ISO format date string
            
        Raises:
            InvalidInputError: If date is invalid
        """
        if isinstance(value, date):
            return value.isoformat()
        
        if isinstance(value, datetime):
            return value.date().isoformat()
        
        if not isinstance(value, str):
            raise InvalidInputError(f"{slot_name} must be a date string")
        
        value = value.strip()
        
        # Try to parse date
        try:
            parsed_date = parser.parse(value, fuzzy=False)
            return parsed_date.date().isoformat()
        except (ValueError, TypeError) as e:
            raise InvalidInputError(f"{slot_name} has invalid date format: {value}")
    
    def _validate_number(self, slot_name: str, value: Any) -> float:
        """
        Validate number slot.
        
        Args:
            slot_name: Slot name
            value: Number value
            
        Returns:
            Validated number (float)
            
        Raises:
            InvalidInputError: If number is invalid
        """
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            raise InvalidInputError(f"{slot_name} must be a number")
        
        value = value.strip()
        
        # Remove common formatting
        value = value.replace(",", "").replace(" ", "")
        
        try:
            return float(value)
        except (ValueError, TypeError):
            raise InvalidInputError(f"{slot_name} has invalid number format: {value}")
    
    def _validate_email(self, slot_name: str, value: Any) -> str:
        """
        Validate email slot.
        
        Args:
            slot_name: Slot name
            value: Email value
            
        Returns:
            Validated email string
            
        Raises:
            InvalidInputError: If email is invalid
        """
        if not isinstance(value, str):
            raise InvalidInputError(f"{slot_name} must be an email string")
        
        value = value.strip().lower()
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise InvalidInputError(f"{slot_name} has invalid email format: {value}")
        
        return value
    
    def _validate_phone(self, slot_name: str, value: Any) -> str:
        """
        Validate phone slot.
        
        Args:
            slot_name: Slot name
            value: Phone value
            
        Returns:
            Validated phone string (normalized)
            
        Raises:
            InvalidInputError: If phone is invalid
        """
        if not isinstance(value, str):
            raise InvalidInputError(f"{slot_name} must be a phone string")
        
        value = value.strip()
        
        # Remove common formatting
        value = re.sub(r'[\s\-\(\)]', '', value)
        
        # Check if it's all digits (with optional + prefix)
        if value.startswith('+'):
            digits = value[1:]
        else:
            digits = value
        
        if not digits.isdigit() or len(digits) < 8:
            raise InvalidInputError(f"{slot_name} has invalid phone format: {value}")
        
        return value


# Global validator instance
slot_validator = SlotValidator()
