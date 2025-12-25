"""
Audit Helper - Convenience functions for audit logging
Priority 2 Fix: Centralized audit logging helpers
"""

from typing import Optional, Dict, Any
from backend.domain.tenant.audit_service import TenantAuditService
from backend.infrastructure.database_client import database_client
from backend.shared.logger import logger


async def log_tenant_operation(
    tenant_id: str,
    operation: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_key: Optional[str] = None,
    channel: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Helper function to log tenant operations.
    
    This is a convenience wrapper that:
    - Gets database connection
    - Creates audit service
    - Logs the operation
    - Handles errors gracefully (doesn't fail if audit logging fails)
    
    Args:
        tenant_id: Tenant UUID
        operation: Operation type (create, update, delete, read, message, etc.)
        resource_type: Type of resource (tenant, product, conversation, etc.)
        resource_id: ID of the resource
        user_key: User who performed the operation
        channel: Channel (web, telegram, teams, api)
        ip_address: Client IP address
        request_id: Correlation ID for tracing
        metadata: Additional context data
    
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        if not database_client.pool:
            logger.warning("Database pool not available for audit logging")
            return False
        
        async with database_client.pool.acquire() as conn:
            audit_service = TenantAuditService(conn)
            return await audit_service.log_operation(
                tenant_id=tenant_id,
                operation=operation,
                resource_type=resource_type,
                resource_id=resource_id,
                user_key=user_key,
                channel=channel,
                ip_address=ip_address,
                request_id=request_id,
                metadata=metadata,
            )
    except Exception as e:
        # Don't fail the operation if audit logging fails
        logger.warning(f"Failed to log audit entry: {e}", exc_info=True)
        return False

