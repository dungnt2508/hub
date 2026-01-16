"""
Domain Specifications - Metadata definitions for domains and intents

This module defines the structure for domain and intent metadata,
completely decoupled from runtime handlers.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class DomainType(str, Enum):
    """Domain type classification"""
    OPERATION = "OPERATION"  # Domain with discrete operations/intents
    STATEFUL = "STATEFUL"  # Domain with stateful interactions (no fixed intents)
    KNOWLEDGE = "KNOWLEDGE"  # Domain for knowledge queries
    META = "META"  # Meta domain for system tasks


class InteractionMode(str, Enum):
    """How users interact with the domain"""
    COMMAND = "COMMAND"  # User issues commands (OPERATION domains)
    EXPLORE = "EXPLORE"  # User explores/browses (STATEFUL domains)
    QUERY = "QUERY"  # User queries knowledge (KNOWLEDGE domains)
    CONVERSATIONAL = "CONVERSATIONAL"  # Conversational (META domains)


class UIMode(str, Enum):
    """UI presentation mode for frontend"""
    FORM = "FORM"  # Form-based UI (OPERATION with slots)
    EXPLORE = "EXPLORE"  # Explore/browse UI (STATEFUL)
    CHAT = "CHAT"  # Chat interface (KNOWLEDGE, META)
    DASHBOARD = "DASHBOARD"  # Dashboard UI (OPERATION with results)


@dataclass
class IntentSpec:
    """
    Specification for an intent (only for OPERATION domains).
    
    STATEFUL domains do not have intent specs.
    """
    intent: str
    display_name: str
    description: str
    command_type: Optional[str] = None  # Optional: e.g., "CREATE", "QUERY", "UPDATE"
    requires_slots: bool = False
    slot_names: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainSpec:
    """
    Specification for a domain - pure metadata, no runtime coupling.
    
    This is the source of truth for domain metadata, completely
    decoupled from entry handlers.
    """
    name: str
    display_name: str
    description: str
    domain_type: DomainType
    interaction_mode: InteractionMode
    ui_mode: UIMode
    intents: List[IntentSpec] = field(default_factory=list)  # Only for OPERATION domains
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_intents(self) -> bool:
        """Check if domain has intent list (OPERATION domains only)"""
        return self.domain_type == DomainType.OPERATION and len(self.intents) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses"""
        result = {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "domain_type": self.domain_type.value,
            "interaction_mode": self.interaction_mode.value,
            "ui_mode": self.ui_mode.value,
            "metadata": self.metadata,
        }
        
        # Only include intents for OPERATION domains
        if self.has_intents():
            result["intents"] = [
                {
                    "intent": intent.intent,
                    "display_name": intent.display_name,
                    "description": intent.description,
                    "command_type": intent.command_type,
                    "requires_slots": intent.requires_slots,
                    "slot_names": intent.slot_names,
                    "metadata": intent.metadata,
                }
                for intent in self.intents
            ]
        else:
            result["intents"] = []
        
        return result
