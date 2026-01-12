"""
DBA Use Case Metadata Registry - Single Source of Truth for Use Case Metadata

This module provides centralized metadata management for DBA use cases.
All use case metadata (name, description, icon, slots, playbook) is defined here.
"""
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field

from .use_cases.base_use_case import BaseUseCase
from ...shared.logger import logger


@dataclass
class UseCaseMetadata:
    """Metadata for a DBA use case"""
    id: str  # Use case ID (e.g., "analyze_slow_query")
    name: str  # Display name (e.g., "Analyze Slow Queries")
    description: str  # Description for frontend
    icon: str  # Icon emoji/character
    intent: str  # Intent name (usually same as id)
    required_slots: List[str]  # Required slots
    optional_slots: List[str]  # Optional slots
    source_allowed: List[str]  # Allowed sources (e.g., ["OPERATION"])
    playbook_name: Optional[str] = None  # Playbook name for execution (e.g., "QUERY_PERFORMANCE")
    use_case_class: Optional[Type[BaseUseCase]] = None  # Use case class (set during registration)
    
    # Extended metadata for frontend
    tags: List[str] = field(default_factory=list)  # Tags for categorization
    param_schema: Optional[Dict[str, Any]] = None  # JSON schema for parameters
    editable_query_schema: Optional[Dict[str, Any]] = None  # Schema for query editing (if allowed)
    output_schema: Optional[Dict[str, Any]] = None  # JSON schema for output structure
    execution_limits: Optional[Dict[str, Any]] = None  # Execution limits (timeout, max_rows, etc.)
    capability_flags: Optional[Dict[str, bool]] = None  # Feature flags (can_edit_query, can_export, etc.)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API response"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "intent": self.intent,
            "required_slots": self.required_slots,
            "optional_slots": self.optional_slots,
            "source_allowed": self.source_allowed,
            "playbook_name": self.playbook_name,
            "tags": self.tags,
            "param_schema": self.param_schema,
            "editable_query_schema": self.editable_query_schema,
            "output_schema": self.output_schema,
            "execution_limits": self.execution_limits,
            "capability_flags": self.capability_flags,
        }


class DBAUseCaseMetadataRegistry:
    """
    Registry for DBA use case metadata.
    
    Single source of truth for all use case metadata.
    """
    
    _metadata: Dict[str, UseCaseMetadata] = {}
    
    @classmethod
    def register(
        cls,
        use_case_id: str,
        name: str,
        description: str,
        icon: str,
        required_slots: List[str],
        optional_slots: List[str],
        source_allowed: List[str] = None,
        playbook_name: Optional[str] = None,
        use_case_class: Optional[Type[BaseUseCase]] = None,
        tags: Optional[List[str]] = None,
        param_schema: Optional[Dict[str, Any]] = None,
        editable_query_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        execution_limits: Optional[Dict[str, Any]] = None,
        capability_flags: Optional[Dict[str, bool]] = None,
    ) -> UseCaseMetadata:
        """
        Register use case metadata.
        
        Args:
            use_case_id: Use case ID (e.g., "analyze_slow_query")
            name: Display name
            description: Description
            icon: Icon emoji
            required_slots: Required slots
            optional_slots: Optional slots
            source_allowed: Allowed sources (default: ["OPERATION"])
            playbook_name: Playbook name for execution
            use_case_class: Use case class (optional, can be set later)
            
        Returns:
            UseCaseMetadata instance
        """
        if source_allowed is None:
            source_allowed = ["OPERATION"]
        
        metadata = UseCaseMetadata(
            id=use_case_id,
            name=name,
            description=description,
            icon=icon,
            intent=use_case_id,
            required_slots=required_slots,
            optional_slots=optional_slots,
            source_allowed=source_allowed,
            playbook_name=playbook_name,
            use_case_class=use_case_class,
            tags=tags or [],
            param_schema=param_schema,
            editable_query_schema=editable_query_schema,
            output_schema=output_schema,
            execution_limits=execution_limits,
            capability_flags=capability_flags,
        )
        
        cls._metadata[use_case_id] = metadata
        
        logger.debug(f"Registered use case metadata: {use_case_id}")
        
        return metadata
    
    @classmethod
    def get(cls, use_case_id: str) -> Optional[UseCaseMetadata]:
        """Get metadata for a use case"""
        return cls._metadata.get(use_case_id)
    
    @classmethod
    def get_all(cls) -> List[UseCaseMetadata]:
        """Get all registered metadata"""
        return list(cls._metadata.values())
    
    @classmethod
    def get_playbook_name(cls, use_case_id: str) -> Optional[str]:
        """Get playbook name for a use case"""
        metadata = cls.get(use_case_id)
        return metadata.playbook_name if metadata else None
    
    @classmethod
    def set_use_case_class(cls, use_case_id: str, use_case_class: Type[BaseUseCase]):
        """Set use case class for metadata (called during entry handler initialization)"""
        metadata = cls.get(use_case_id)
        if metadata:
            metadata.use_case_class = use_case_class
        else:
            logger.warning(f"Trying to set class for unregistered use case: {use_case_id}")


# Global registry instance
dba_use_case_metadata_registry = DBAUseCaseMetadataRegistry()


def use_case_metadata(
    use_case_id: str,
    name: str,
    description: str,
    icon: str,
    required_slots: List[str],
    optional_slots: List[str],
    source_allowed: List[str] = None,
    playbook_name: Optional[str] = None,
):
    """
    Decorator to register use case metadata.
    
    Usage:
        @use_case_metadata(
            use_case_id="analyze_slow_query",
            name="Analyze Slow Queries",
            description="Find slow running queries on database",
            icon="📊",
            required_slots=["db_type"],
            optional_slots=["connection_id", "limit", "min_duration_ms"],
            playbook_name="QUERY_PERFORMANCE"
        )
        class AnalyzeSlowQueryUseCase(BaseUseCase):
            ...
    """
    def decorator(cls: Type[BaseUseCase]):
        dba_use_case_metadata_registry.register(
            use_case_id=use_case_id,
            name=name,
            description=description,
            icon=icon,
            required_slots=required_slots,
            optional_slots=optional_slots,
            source_allowed=source_allowed,
            playbook_name=playbook_name,
            use_case_class=cls,
            tags=tags,
            param_schema=param_schema,
            editable_query_schema=editable_query_schema,
            output_schema=output_schema,
            execution_limits=execution_limits,
            capability_flags=capability_flags,
        )
        return cls
    
    return decorator

