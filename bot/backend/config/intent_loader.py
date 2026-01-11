"""
Intent Registry Loader - Load intents from YAML configuration
"""
from typing import List, Dict, Any
import yaml
import os
from pathlib import Path


def _validate_intent(intent_dict: Dict[str, Any]) -> None:
    """
    Validate intent definition schema.
    
    Args:
        intent_dict: Intent definition from YAML
        
    Raises:
        ValueError: If intent schema is invalid
    """
    intent_name = intent_dict.get('intent', 'UNKNOWN')
    
    # Check required fields
    required_fields = ['intent', 'domain', 'intent_type', 'source_allowed']
    for field in required_fields:
        if field not in intent_dict:
            raise ValueError(f"Intent '{intent_name}' missing required field: {field}")
    
    # Validate intent_type
    valid_types = ['OPERATION', 'KNOWLEDGE']
    if intent_dict['intent_type'] not in valid_types:
        raise ValueError(
            f"Intent '{intent_name}' has invalid intent_type: {intent_dict['intent_type']}. "
            f"Must be one of: {valid_types}"
        )
    
    # Validate source_allowed
    valid_sources = ['PATTERN', 'EMBEDDING', 'LLM']
    sources = intent_dict.get('source_allowed', [])
    if not isinstance(sources, list):
        raise ValueError(f"Intent '{intent_name}' source_allowed must be a list")
    
    for source in sources:
        if source not in valid_sources:
            raise ValueError(
                f"Intent '{intent_name}' has invalid source: {source}. "
                f"Must be one of: {valid_sources}"
            )
    
    # Validate slots don't overlap
    required_slots = set(intent_dict.get('required_slots', []))
    optional_slots = set(intent_dict.get('optional_slots', []))
    overlap = required_slots & optional_slots
    if overlap:
        raise ValueError(
            f"Intent '{intent_name}' has overlapping required and optional slots: {overlap}"
        )


def load_intents_from_yaml() -> List[Dict[str, Any]]:
    """
    Load and validate intents from intent_registry.yaml
    
    Returns:
        List of validated intent dictionaries
        
    Raises:
        FileNotFoundError: If YAML not found
        ValueError: If YAML is invalid
    """
    from ..shared.logger import logger
    
    try:
        # Find intent_registry.yaml
        config_path = Path(__file__).parent.parent.parent / 'config' / 'intent_registry.yaml'
        
        if not config_path.exists():
            # Fallback: try relative to current directory
            config_path = Path('bot/config/intent_registry.yaml')
            
        if not config_path.exists():
            # Last resort: try from environment
            env_path = os.getenv('INTENT_REGISTRY_PATH')
            if env_path:
                config_path = Path(env_path)
            else:
                raise FileNotFoundError(
                    "intent_registry.yaml not found. "
                    "Please set INTENT_REGISTRY_PATH env var or place YAML in bot/config/"
                )
        
        # Load YAML
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data or 'intents' not in data:
            raise ValueError("intent_registry.yaml must contain 'intents' list")
        
        intents = data['intents']
        if not intents:
            raise ValueError("intent_registry.yaml 'intents' list is empty")
        
        # Validate each intent
        for intent_dict in intents:
            try:
                _validate_intent(intent_dict)
            except ValueError as e:
                raise ValueError(f"Invalid intent in YAML: {e}") from e
        
        logger.info(f"Loaded {len(intents)} intents from {config_path}")
        return intents
    
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading intents from YAML: {e}", exc_info=True)
        raise ValueError(f"Failed to load intent registry: {e}") from e


def _get_default_intents() -> List[Dict[str, Any]]:
    """
    Get minimal fallback intents.
    
    NOTE: This should rarely be used. Intent registry YAML is required.
    If we reach here, there's a startup configuration problem.
    """
    logger.warning(
        "Using minimal fallback intents - intent_registry.yaml should be loaded"
    )
    # Return empty list instead of duplicating YAML data
    # This forces the system to fail-fast if YAML is missing
    return []
