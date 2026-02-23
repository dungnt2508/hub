from fastapi import Request, HTTPException, status
from typing import Optional

async def get_current_tenant_id(request: Request) -> str:
    """
    Dependency to get the current tenant ID from the request state.
    The tenant ID is populated by the AuthMiddleware (from JWT).
    NO fallback to X-Tenant-ID header - security: prevents tenant spoofing.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant identification missing. Valid JWT required."
        )
    return tenant_id
