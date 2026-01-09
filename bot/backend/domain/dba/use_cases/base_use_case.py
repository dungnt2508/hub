"""
Base Use Case for DBA Domain
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

from ....schemas import DomainRequest, DomainResponse


class BaseUseCase(ABC):
    """Base class for all DBA use cases"""
    
    @abstractmethod
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute use case.
        
        Args:
            request: Domain request
            
        Returns:
            Domain response
        """
        pass
    
    def validate_slots(
        self,
        request: DomainRequest,
        required_slots: list[str]
    ) -> list[str]:
        """
        Validate required slots.
        
        Args:
            request: Domain request
            required_slots: List of required slot names
            
        Returns:
            List of missing slot names
        """
        missing = []
        for slot in required_slots:
            if slot not in request.slots or request.slots[slot] is None:
                missing.append(slot)
        return missing

