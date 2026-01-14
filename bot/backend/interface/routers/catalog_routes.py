"""
Catalog API Routes - Endpoints for catalog domain sandbox and testing
"""
from fastapi import APIRouter, HTTPException, Request, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

from ...schemas import DomainRequest, DomainResult
from ...domain.catalog.entry_handler import CatalogEntryHandler
from ...domain.catalog.intent_classifier import CatalogIntentClassifier
from ...shared.logger import logger
from ...shared.exceptions import DomainError, InvalidInputError
from ...shared.request_metadata import RequestMetadata

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class CatalogQueryRequest(BaseModel):
    """Request model for catalog query"""
    question: str = Field(..., min_length=1, max_length=1000, description="User question about products")
    tenant_id: Optional[str] = Field(None, description="Tenant UUID (optional, can be extracted from request)")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")


class CatalogQueryResponse(BaseModel):
    """Response model for catalog query"""
    answer: str
    intent_type: Optional[str] = None
    retrieval_method: Optional[str] = None
    products_found: int = 0
    confidence: float = 0.0
    classification: Optional[Dict[str, Any]] = None
    sources: Optional[list] = None
    trace_id: Optional[str] = None


class IntentClassificationRequest(BaseModel):
    """Request model for intent classification only"""
    question: str = Field(..., min_length=1, max_length=1000)


class IntentClassificationResponse(BaseModel):
    """Response model for intent classification"""
    intent_type: str
    confidence: float
    reason: str
    extracted_info: Dict[str, Any]


# ============================================================
# CATALOG QUERY ENDPOINT
# ============================================================

@router.post("/query", response_model=CatalogQueryResponse)
async def query_catalog(
    request: CatalogQueryRequest,
    raw_request: Request,
):
    """
    POST /api/catalog/query
    
    Query catalog domain with intent classification and hybrid search.
    
    This endpoint is for testing/sandbox purposes.
    For production, use /bot/message which goes through full routing flow.
    
    Request:
    {
        "question": "Giá của ChatGPT bao nhiêu?",
        "tenant_id": "optional-uuid",
        "session_id": "optional-session-id"
    }
    
    Response:
    {
        "answer": "ChatGPT có giá $20/tháng",
        "intent_type": "PRODUCT_SPECIFIC_INFO",
        "retrieval_method": "hybrid_search",
        "products_found": 1,
        "confidence": 0.95,
        "classification": {...},
        "sources": [...]
    }
    """
    try:
        # Extract tenant_id from request metadata if not provided
        tenant_id = request.tenant_id
        if not tenant_id:
            try:
                # Try to extract from headers or query params
                tenant_id = raw_request.headers.get("X-Tenant-Id") or raw_request.query_params.get("tenant_id")
            except Exception as e:
                logger.warning(f"Failed to extract tenant_id from request: {e}")
        
        if not tenant_id:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required. Provide in request body or ensure it's in request metadata."
            )
        
        # Create domain request
        domain_request = DomainRequest(
            domain="catalog",
            intent="catalog.search",  # Default intent, will be mapped by entry handler
            intent_type="KNOWLEDGE",
            slots={
                "question": request.question,
                "query": request.question,
            },
            user_context={
                "tenant_id": tenant_id,
                "user_id": "sandbox-test",
                "session_id": request.session_id,
            },
            trace_id=f"catalog-query-{raw_request.headers.get('x-request-id', 'unknown')}",
        )
        
        # Handle via CatalogEntryHandler
        handler = CatalogEntryHandler()
        response = await handler.handle(domain_request)
        
        # Format response for frontend
        if response.status != DomainResult.SUCCESS:
            raise HTTPException(
                status_code=400 if response.status == DomainResult.INVALID_REQUEST else 500,
                detail=response.message or "Catalog query failed"
            )
        
        # Extract classification info if available
        classification = None
        if response.audit:
            # Try to get classification from audit or data
            classification = response.audit.get("classification")
            if not classification and response.data:
                # Build classification from response data
                classification = {
                    "intent_type": response.audit.get("intent_type", "unknown"),
                    "confidence": response.audit.get("confidence", 0.0),
                }
        
        return CatalogQueryResponse(
            answer=response.message or "Không tìm thấy thông tin.",
            intent_type=response.audit.get("intent_type") if response.audit else None,
            retrieval_method=response.audit.get("retrieval_method") if response.audit else None,
            products_found=response.audit.get("products_found", 0) if response.audit else 0,
            confidence=response.audit.get("confidence", 0.0) if response.audit else 0.0,
            classification=classification,
            sources=response.data.get("sources") if response.data else None,
            trace_id=domain_request.trace_id,
        )
        
    except HTTPException:
        raise
    except InvalidInputError as e:
        logger.warning(f"Invalid catalog query request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except DomainError as e:
        logger.error(f"Catalog domain error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Catalog domain processing failed")
    except Exception as e:
        logger.error(f"Unexpected error in catalog query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================
# INTENT CLASSIFICATION ENDPOINT
# ============================================================

@router.post("/classify-intent", response_model=IntentClassificationResponse)
async def classify_intent(request: IntentClassificationRequest):
    """
    POST /api/catalog/classify-intent
    
    Classify catalog query intent without executing full pipeline.
    Useful for testing intent classification.
    
    Request:
    {
        "question": "Tính năng nào của Claude?"
    }
    
    Response:
    {
        "intent_type": "PRODUCT_SPECIFIC_INFO",
        "confidence": 0.90,
        "reason": "Hỏi về tính năng",
        "extracted_info": {
            "attribute": "features"
        }
    }
    """
    try:
        classifier = CatalogIntentClassifier()
        result = await classifier.classify(request.question)
        
        return IntentClassificationResponse(
            intent_type=result.intent_type.value,
            confidence=result.confidence,
            reason=result.reason,
            extracted_info=result.extracted_info,
        )
        
    except Exception as e:
        logger.error(f"Intent classification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Intent classification failed")


# ============================================================
# CATALOG STATS ENDPOINT (Optional)
# ============================================================

@router.get("/stats")
async def get_catalog_stats(tenant_id: Optional[str] = None):
    """
    GET /api/catalog/stats
    
    Get catalog statistics (optional endpoint for sandbox).
    
    Query params:
    - tenant_id: Optional tenant UUID
    """
    try:
        # For now, return basic stats
        # TODO: Implement actual stats from repository
        return {
            "status": "success",
            "message": "Catalog stats endpoint (placeholder)",
            "stats": {
                "total_products": 0,
                "tenant_id": tenant_id,
            }
        }
    except Exception as e:
        logger.error(f"Error getting catalog stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get catalog stats")

