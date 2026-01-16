"""
Intent Registry Loader
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class IntentInfo:
    """Intent information"""
    intent: str
    domain: str
    intent_type: str
    required_slots: list[str]
    optional_slots: list[str]
    source_allowed: list[str]
    description: str
    use_case_key: Optional[str] = None  # For domain-specific use case mapping


class IntentRegistry:
    """Intent registry - single source of truth"""
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize intent registry.
        
        Args:
            registry_path: Path to intent_registry.yaml file
        """
        if registry_path is None:
            # Default path
            registry_path = Path(__file__).parent.parent.parent / "config" / "intent_registry.yaml"
        
        self.registry_path = Path(registry_path)
        self.intents: Dict[str, IntentInfo] = {}
        self._load()
    
    def _load(self):
        """Load intent registry from YAML file"""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Intent registry not found: {self.registry_path}")
        
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        for intent_data in data.get("intents", []):
            intent_info = IntentInfo(
                intent=intent_data["intent"],
                domain=intent_data["domain"],
                intent_type=intent_data["intent_type"],
                required_slots=intent_data.get("required_slots", []),
                optional_slots=intent_data.get("optional_slots", []),
                source_allowed=intent_data.get("source_allowed", []),
                description=intent_data.get("description", ""),
                use_case_key=intent_data.get("use_case_key"),
            )
            self.intents[intent_info.intent] = intent_info
    
    def get_intent(self, intent_name: str) -> Optional[IntentInfo]:
        """Get intent information"""
        return self.intents.get(intent_name)
    
    def is_valid_intent(self, intent_name: str) -> bool:
        """Check if intent exists in registry"""
        return intent_name in self.intents
    
    def get_intents_by_domain(self, domain: str) -> list[IntentInfo]:
        """Get all intents for a domain"""
        return [
            intent_info
            for intent_info in self.intents.values()
            if intent_info.domain == domain
        ]
    
    def is_source_allowed(self, intent_name: str, source: str) -> bool:
        """Check if source is allowed for intent"""
        intent_info = self.get_intent(intent_name)
        if not intent_info:
            return False
        return source in intent_info.source_allowed
    
    def get_use_case_key(self, intent_name: str) -> Optional[str]:
        """
        Get use case key for intent (domain-specific mapping).
        
        Args:
            intent_name: Intent name
            
        Returns:
            Use case key if found, None otherwise
        """
        intent_info = self.get_intent(intent_name)
        if not intent_info:
            return None
        return intent_info.use_case_key


# Global registry instance
intent_registry = IntentRegistry()

