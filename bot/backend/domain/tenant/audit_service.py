"""
Tenant Audit Service - Log all tenant operations for security and compliance
Priority 2 Fix: Implement audit logging
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import json

from backend.shared.logger import logger


class TenantAuditService:
    """
    Service for logging tenant operations.
    
    Logs all operations performed by tenants for:
    - Security auditing
    - Compliance tracking
    - Debugging
    - Analytics
    """
    
    def __init__(self, db_connection):
        """
        Initialize audit service.
        
        Args:
            db_connection: PostgreSQL connection pool
        """
        self.db = db_connection
        logger.info("TenantAuditService initialized")
    
    async def log_operation(
        self,
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
        Log a tenant operation.
        
        Args:
            tenant_id: Tenant UUID
            operation: Operation type (e.g., 'create', 'update', 'delete', 'read')
            resource_type: Type of resource (e.g., 'tenant', 'product', 'conversation')
            resource_id: ID of the resource
            user_key: User who performed the operation
            channel: Channel (web, telegram, teams, api)
            ip_address: Client IP address
            request_id: Correlation ID for tracing
            metadata: Additional context data
        
        Returns:
            True if logged successfully
        """
        try:
            log_id = str(uuid.uuid4())
            
            # Serialize metadata dict to JSON string for JSONB column
            metadata_json = json.dumps(metadata) if metadata else None
            
            query = """
            INSERT INTO tenant_audit_logs (
                id, tenant_id, operation, resource_type, resource_id,
                user_key, channel, ip_address, request_id, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
            """
            
            await self.db.execute(
                query,
                log_id,
                tenant_id,
                operation,
                resource_type,
                resource_id,
                user_key,
                channel,
                ip_address,
                request_id,
                metadata_json,
                datetime.now(),
            )
            
            logger.debug(
                f"Audit log created: {operation} on {resource_type}",
                extra={
                    "tenant_id": tenant_id,
                    "operation": operation,
                    "resource_type": resource_type,
                }
            )
            
            return True
        
        except Exception as e:
            # Don't fail the operation if audit logging fails
            logger.error(f"Failed to log audit entry: {e}", exc_info=True)
            return False
    
    async def get_audit_logs(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
        operation: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs for a tenant.
        
        Args:
            tenant_id: Tenant UUID
            limit: Number of logs to return
            offset: Pagination offset
            operation: Filter by operation type
            resource_type: Filter by resource type
            start_date: Filter logs after this date
            end_date: Filter logs before this date
        
        Returns:
            List of audit log entries
        """
        try:
            conditions = ["tenant_id = $1"]
            values = [tenant_id]
            param_index = 2
            
            if operation:
                conditions.append(f"operation = ${param_index}")
                values.append(operation)
                param_index += 1
            
            if resource_type:
                conditions.append(f"resource_type = ${param_index}")
                values.append(resource_type)
                param_index += 1
            
            if start_date:
                conditions.append(f"created_at >= ${param_index}")
                values.append(start_date)
                param_index += 1
            
            if end_date:
                conditions.append(f"created_at <= ${param_index}")
                values.append(end_date)
                param_index += 1
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
            SELECT id, tenant_id, operation, resource_type, resource_id,
                   user_key, channel, ip_address, request_id, metadata, created_at
            FROM tenant_audit_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_index} OFFSET ${param_index + 1}
            """
            
            values.extend([limit, offset])
            
            rows = await self.db.fetch(query, *values)
            
            return [
                {
                    "id": str(row['id']),
                    "tenant_id": str(row['tenant_id']),
                    "operation": row['operation'],
                    "resource_type": row['resource_type'],
                    "resource_id": str(row['resource_id']) if row['resource_id'] else None,
                    "user_key": row['user_key'],
                    "channel": row['channel'],
                    "ip_address": row['ip_address'],
                    "request_id": row['request_id'],
                    "metadata": row['metadata'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                }
                for row in rows
            ]
        
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}", exc_info=True)
            return []

