"""
Slot Validator - Validate slots against intent schema
"""
from typing import Dict, Any, Optional

from .exceptions import InvalidInputError
from .logger import logger
from .intent_registry import intent_registry


class SlotValidator:
    """
    Validate slots against intent schema (required, optional, types).
    
    This is used to validate slots extracted from patterns or returned from steps.
    """
    
    @staticmethod
    def validate(
        slots: Dict[str, Any],
        intent: str,
        raise_on_missing_required: bool = True
    ) -> Dict[str, Any]:
        """
        Validate slots against intent schema.
        
        Args:
            slots: Slots to validate
            intent: Intent name to get schema for
            raise_on_missing_required: If True, raise error on missing required slots
                                       If False, log warning
            
        Returns:
            Validated slots dict
            
        Raises:
            InvalidInputError: If validation fails and raise_on_missing_required=True
        """
        if not intent:
            raise InvalidInputError("intent is required for slot validation")
        
        # Get intent schema
        intent_def = intent_registry.get_intent(intent)
        if not intent_def:
            raise InvalidInputError(f"Unknown intent: {intent}")
        
        # Check required slots
        required_slots = intent_def.required_slots or []
        optional_slots = intent_def.optional_slots or []
        
        missing_required = []
        for slot_name in required_slots:
            if slot_name not in slots:
                missing_required.append(slot_name)
        
        if missing_required:
            msg = f"Intent '{intent}' missing required slots: {missing_required}"
            if raise_on_missing_required:
                logger.warning(msg)
                raise InvalidInputError(msg)
            else:
                logger.warning(msg)
        
        # Filter slots to only include defined slots
        allowed_slots = set(required_slots + optional_slots)
        filtered_slots = {}
        unknown_slots = []
        
        for slot_name, slot_value in slots.items():
            if slot_name in allowed_slots:
                filtered_slots[slot_name] = slot_value
            else:
                unknown_slots.append(slot_name)
        
        if unknown_slots:
            logger.warning(
                f"Intent '{intent}' has unknown slots: {unknown_slots}. Ignored."
            )
        
        return filtered_slots
    
    @staticmethod
    def get_missing_required_slots(
        slots: Dict[str, Any],
        intent: str
    ) -> list:
        """
        Get list of missing required slots.
        
        Args:
            slots: Current slots
            intent: Intent name
            
        Returns:
            List of missing required slot names
        """
        intent_def = intent_registry.get_intent(intent)
        if not intent_def:
            return []
        
        required_slots = intent_def.required_slots or []
        return [s for s in required_slots if s not in slots]
