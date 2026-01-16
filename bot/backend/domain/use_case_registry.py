"""
Use Case Registry - Backward compatibility wrapper

DEPRECATED: This module is kept for backward compatibility.
New code should use domain_registry from domain_registry.py instead.

This wrapper provides the same API as the old UseCaseRegistry but
delegates to the new DomainRegistry which is decoupled from handlers.
"""
from typing import Dict, List, Any
from .domain_registry import domain_registry
from .domain_specs import DomainType
from ..shared.logger import logger


class UseCaseRegistry:
    """
    Backward compatibility wrapper for UseCaseRegistry.
    
    DEPRECATED: Use domain_registry directly instead.
    
    This class maintains the old API while delegating to the new
    DomainRegistry that is properly decoupled from handlers.
    """
    
    def __init__(self):
        """Initialize - no handler instantiation"""
        logger.warning(
            "UseCaseRegistry is deprecated. Use domain_registry from domain_registry.py instead."
        )
    
    def get_all_domains(self) -> List[Dict[str, Any]]:
        """
        Get all domains with their intents (backward compatible format).
        
        Returns:
            List of domain dicts in old format for backward compatibility
        """
        domains = []
        for domain_spec in domain_registry.get_all_domains():
            domain_dict = domain_spec.to_dict()
            
            # Convert to old format for backward compatibility
            # Map domain_type to old intent_type field
            old_intent_type = self._map_domain_type_to_old_intent_type(domain_spec.domain_type)
            domain_dict["intent_type"] = old_intent_type
            
            # For backward compatibility, ensure intents have intent_type
            for intent in domain_dict.get("intents", []):
                intent["intent_type"] = old_intent_type
            
            domains.append(domain_dict)
        
        return domains
    
    def get_domain(self, domain_name: str) -> Dict[str, Any]:
        """
        Get specific domain (backward compatible format).
        
        Returns:
            Domain dict in old format, or empty dict if not found
        """
        domain_spec = domain_registry.get_domain(domain_name)
        if not domain_spec:
            return {}
        
        domain_dict = domain_spec.to_dict()
        
        # Convert to old format for backward compatibility
        old_intent_type = self._map_domain_type_to_old_intent_type(domain_spec.domain_type)
        domain_dict["intent_type"] = old_intent_type
        
        # For backward compatibility, ensure intents have intent_type
        for intent in domain_dict.get("intents", []):
            intent["intent_type"] = old_intent_type
        
        return domain_dict
    
    def get_all_intents(self) -> List[Dict[str, Any]]:
        """
        Get all intents across all domains (backward compatible format).
        
        Note: STATEFUL domains (like Catalog) will not appear here
        as they don't have fixed intents.
        """
        intents = domain_registry.get_all_intents()
        
        # Add intent_type for backward compatibility
        for intent in intents:
            domain_spec = domain_registry.get_domain(intent["domain"])
            if domain_spec:
                intent["intent_type"] = self._map_domain_type_to_old_intent_type(domain_spec.domain_type)
        
        return intents
    
    def get_intents_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        """
        Get intents for specific domain (backward compatible format).
        
        Returns empty list for STATEFUL, KNOWLEDGE, or META domains.
        """
        intents = domain_registry.get_intents_by_domain(domain_name)
        
        # Add intent_type for backward compatibility
        domain_spec = domain_registry.get_domain(domain_name)
        if domain_spec:
            old_intent_type = self._map_domain_type_to_old_intent_type(domain_spec.domain_type)
            for intent in intents:
                intent["intent_type"] = old_intent_type
        
        return intents
    
    @staticmethod
    def _map_domain_type_to_old_intent_type(domain_type: DomainType) -> str:
        """
        Map new DomainType to old intent_type string for backward compatibility.
        
        This maintains the old API format while using the new architecture.
        """
        mapping = {
            DomainType.OPERATION: "OPERATION",
            DomainType.STATEFUL: "KNOWLEDGE",  # Catalog was marked as KNOWLEDGE in old code
            DomainType.KNOWLEDGE: "KNOWLEDGE",
            DomainType.META: "META",
        }
        return mapping.get(domain_type, "OPERATION")


# Global registry instance (backward compatibility)
use_case_registry = UseCaseRegistry()

