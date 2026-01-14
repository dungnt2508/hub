"""
Catalog Domain Engine - Entry Handler
"""
from typing import Dict, Any, Optional

from ...schemas import DomainRequest, DomainResponse, DomainResult
from ...shared.exceptions import DomainError, InvalidInputError
from ...shared.logger import logger
from .adapters.catalog_repository import CatalogRepositoryAdapter
from .use_cases import (
    SearchProductUseCase,
    GetProductInfoUseCase,
    CompareProductsUseCase,
    CheckAvailabilityUseCase,
    GetProductPriceUseCase,
)


class CatalogEntryHandler:
    """
    Entry point for catalog domain engine.
    
    Maps router intents to use cases and executes them.
    Following Clean Architecture:
    - Entry handler = Application layer (orchestration)
    - Use cases = Domain layer (business logic)
    - Repository adapter = Infrastructure layer (data access)
    """
    
    def __init__(
        self,
        repository: Optional[CatalogRepositoryAdapter] = None,
    ):
        """
        Initialize catalog entry handler.
        
        Args:
            repository: Optional repository adapter (defaults to CatalogRepositoryAdapter)
        """
        # Initialize repository if not provided
        if repository is None:
            repository = CatalogRepositoryAdapter()
        
        # Initialize use cases with repository injection
        self.use_cases = {
            "catalog.search": SearchProductUseCase(repository),
            "catalog.info": GetProductInfoUseCase(repository),
            "catalog.compare": CompareProductsUseCase(repository),
            "catalog.availability": CheckAvailabilityUseCase(repository),
            "catalog.price": GetProductPriceUseCase(repository),
        }
        
        # Intent mapping: Router intents (from seed data) → Use case keys
        # This maps the intents from pattern rules/routing rules to our use case keys
        self.intent_mapping = {
            # Search intents
            "search_products": "catalog.search",
            "search_by_category": "catalog.search",  # Category search also uses search use case
            
            # Product info intents
            "query_product_detail": "catalog.info",
            "query_variant": "catalog.info",  # Variant query is part of product info
            
            # Price intent
            "query_price": "catalog.price",
            
            # Availability intent
            "check_availability": "catalog.availability",
            
            # Comparison intent
            "compare_products": "catalog.compare",
            
            # Also support direct use case keys (for backward compatibility)
            "catalog.search": "catalog.search",
            "catalog.info": "catalog.info",
            "catalog.compare": "catalog.compare",
            "catalog.availability": "catalog.availability",
            "catalog.price": "catalog.price",
        }
        
        logger.info(
            "CatalogEntryHandler initialized",
            extra={
                "use_cases": list(self.use_cases.keys()),
                "intent_mapping": list(self.intent_mapping.keys()),
            }
        )
    
    async def handle(self, request: DomainRequest) -> DomainResponse:
        """
        Handle catalog domain request.
        
        Maps router intent to use case and executes it.
        
        Args:
            request: Domain request with intent and slots
        
        Returns:
            Domain response with result
        
        Raises:
            DomainError: If handling fails
        """
        try:
            # Validate request
            validation_error = self._validate_request(request)
            if validation_error:
                return validation_error
            
            logger.info(
                "Catalog domain request received",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                    "intent_type": request.intent_type,
                    "tenant_id": request.user_context.get("tenant_id"),
                }
            )
            
            # Map router intent to use case key
            use_case_key = self.intent_mapping.get(request.intent)
            
            if not use_case_key:
                logger.warning(
                    f"Unknown catalog intent: {request.intent}",
                    extra={
                        "trace_id": request.trace_id,
                        "available_intents": list(self.intent_mapping.keys()),
                    }
                )
                # Fallback to search if intent is unknown
                use_case_key = "catalog.search"
                logger.info(
                    f"Falling back to catalog.search for unknown intent: {request.intent}",
                    extra={"trace_id": request.trace_id}
                )
            
            # Validate use case exists
            if use_case_key not in self.use_cases:
                logger.error(
                    f"Use case not found: {use_case_key}",
                    extra={
                        "trace_id": request.trace_id,
                        "mapped_intent": use_case_key,
                        "original_intent": request.intent,
                    }
                )
                return DomainResponse(
                    status=DomainResult.SYSTEM_ERROR,
                    message=f"Internal error: use case '{use_case_key}' not found",
                    error_code="USE_CASE_NOT_FOUND",
                    error_details={
                        "mapped_intent": use_case_key,
                        "original_intent": request.intent,
                        "available_use_cases": list(self.use_cases.keys()),
                    }
                )
            
            # Get use case
            use_case = self.use_cases[use_case_key]
            
            logger.debug(
                f"Intent mapped: {request.intent} → {use_case_key}",
                extra={
                    "trace_id": request.trace_id,
                    "original_intent": request.intent,
                    "use_case_key": use_case_key,
                }
            )
            
            # Execute use case
            result = await use_case.execute(request)
            
            logger.info(
                "Catalog domain request completed",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                    "status": result.status.value,
                }
            )
            
            return result
            
        except InvalidInputError as e:
            logger.warning(
                f"Invalid catalog request: {e}",
                extra={"trace_id": request.trace_id}
            )
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=str(e),
                error_code="INVALID_INPUT",
            )
        except DomainError as e:
            logger.error(
                f"Catalog domain error: {e}",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                },
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu catalog. Vui lòng thử lại sau.",
                error_code="DOMAIN_ERROR",
                error_details={"error": str(e)},
            )
        except Exception as e:
            logger.error(
                f"Unexpected catalog domain error: {e}",
                extra={
                    "trace_id": request.trace_id,
                    "intent": request.intent,
                },
                exc_info=True
            )
            return DomainResponse(
                status=DomainResult.SYSTEM_ERROR,
                message="Xin lỗi, có lỗi hệ thống xảy ra. Vui lòng thử lại sau.",
                error_code="SYSTEM_ERROR",
                error_details={"error": str(e)},
            )
    
    def _validate_request(self, request: DomainRequest) -> Optional[DomainResponse]:
        """
        Validate domain request before processing.
        
        Args:
            request: Domain request to validate
        
        Returns:
            DomainResponse with error if validation fails, None if valid
        """
        # Validate tenant_id
        tenant_id = request.user_context.get("tenant_id")
        if not tenant_id:
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message="Thiếu thông tin tenant. Vui lòng liên hệ admin.",
                error_code="MISSING_TENANT_ID",
            )
        
        # Validate intent is not empty
        if not request.intent or not request.intent.strip():
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message="Intent không được để trống.",
                error_code="MISSING_INTENT",
            )
        
        # Validate domain matches
        if request.domain != "catalog":
            return DomainResponse(
                status=DomainResult.INVALID_REQUEST,
                message=f"Domain không khớp. Expected: catalog, Got: {request.domain}",
                error_code="DOMAIN_MISMATCH",
            )
        
        return None
