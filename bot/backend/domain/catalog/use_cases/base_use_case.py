"""
Base Use Case for Catalog Domain
"""
from abc import ABC, abstractmethod
from typing import Optional
from ...schemas import DomainRequest, DomainResponse, DomainResult
from ...shared.exceptions import InvalidInputError
from ...shared.logger import logger


class CatalogUseCase(ABC):
    """
    Base use case for catalog domain.
    
    All catalog use cases should inherit from this class.
    Provides common validation and error handling.
    """
    
    @abstractmethod
    async def execute(self, request: DomainRequest) -> DomainResponse:
        """
        Execute use case.
        
        Args:
            request: Domain request with intent and slots
        
        Returns:
            Domain response with result
        
        Raises:
            DomainError: If use case execution fails
        """
        pass
    
    def _extract_tenant_id(self, request: DomainRequest) -> str:
        """
        Extract tenant_id from request with validation.
        
        Args:
            request: Domain request
        
        Returns:
            Tenant ID string
        
        Raises:
            InvalidInputError: If tenant_id is missing
        """
        tenant_id = request.user_context.get("tenant_id")
        if not tenant_id:
            logger.warning(
                "Missing tenant_id in catalog use case",
                extra={"trace_id": request.trace_id}
            )
            raise InvalidInputError("tenant_id is required in user_context")
        
        # Validate tenant_id format (should be UUID string)
        if not isinstance(tenant_id, str) or len(tenant_id.strip()) == 0:
            raise InvalidInputError("tenant_id must be a non-empty string")
        
        return tenant_id.strip()
    
    def _extract_query(self, request: DomainRequest) -> str:
        """
        Extract query/question from request slots with validation.
        
        Args:
            request: Domain request
        
        Returns:
            Query string
        
        Raises:
            InvalidInputError: If query is missing or invalid
        """
        query = (
            request.slots.get("query") or
            request.slots.get("question") or
            request.slots.get("message") or
            ""
        )
        
        query = query.strip() if query else ""
        
        if not query:
            raise InvalidInputError("Query/question is required in slots")
        
        # Validate query length
        if len(query) > 1000:
            raise InvalidInputError("Query/question is too long (max 1000 characters)")
        
        if len(query) < 1:
            raise InvalidInputError("Query/question cannot be empty")
        
        return query
    
    def _extract_product_id(self, request: DomainRequest) -> Optional[str]:
        """Extract product_id from request slots"""
        product_id = request.slots.get("product_id")
        if product_id:
            product_id = product_id.strip()
            if not product_id:
                return None
        return product_id
    
    def _extract_product_name(self, request: DomainRequest) -> Optional[str]:
        """Extract product_name from request slots"""
        product_name = (
            request.slots.get("product_name") or
            request.slots.get("product") or
            None
        )
        if product_name:
            product_name = product_name.strip()
            if not product_name:
                return None
        return product_name
    
    def _create_error_response(
        self,
        request: DomainRequest,
        error_code: str,
        message: str,
        status: DomainResult = DomainResult.SYSTEM_ERROR
    ) -> DomainResponse:
        """
        Create standardized error response.
        
        Args:
            request: Domain request
            error_code: Error code
            message: Error message
            status: Domain result status
        
        Returns:
            Domain response with error
        """
        logger.warning(
            f"Catalog use case error: {error_code}",
            extra={
                "trace_id": request.trace_id,
                "intent": request.intent,
                "error_code": error_code,
            }
        )
        
        return DomainResponse(
            status=status,
            message=message,
            error_code=error_code,
        )

