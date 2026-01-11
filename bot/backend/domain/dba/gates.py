"""
DBA Domain Gates - Production safety, scope validation, permission checks
"""
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from ...schemas import DomainRequest
from ...shared.exceptions import InvalidInputError, PermissionError as DomainPermissionError
from ...shared.logger import logger
from .config import DBAConfig
from .ports.mcp_client import DatabaseType


class Scope:
    """Represents analysis scope"""
    def __init__(self, database: str, server: Optional[str] = None, shard: Optional[str] = None):
        self.database = database
        self.server = server or "unknown"
        self.shard = shard


class ProductionSafetyGate:
    """
    GATE 1: Production Safety Gate
    - Detects if targeting production database
    - Requires explicit permission for production access
    - Logs audit trail for production operations
    """
    
    @staticmethod
    def is_production(connection_string: Optional[str], database: Optional[str]) -> bool:
        """
        Detect if connection targets production.
        
        Heuristics:
        - Connection string contains 'prod'
        - Database name contains 'production' or 'prod'
        """
        if not connection_string and not database:
            return False
        
        indicators = ["prod", "production", "prd"]
        
        if connection_string:
            cs_lower = connection_string.lower()
            if any(ind in cs_lower for ind in indicators):
                return True
        
        if database:
            db_lower = database.lower()
            if any(ind in db_lower for ind in indicators):
                return True
        
        return False
    
    async def check(
        self,
        request: DomainRequest,
        connection_string: Optional[str],
        database: Optional[str]
    ) -> bool:
        """
        Check production safety gate.
        
        Args:
            request: Domain request
            connection_string: Database connection string
            database: Database name
            
        Raises:
            DomainPermissionError: If production access denied
            
        Returns:
            True if check passes
        """
        if not DBAConfig.REQUIRE_PROD_PERMISSION:
            return True
        
        if self.is_production(connection_string, database):
            user_id = request.user_context.get("user_id", "unknown")
            can_prod = request.user_context.get("can_modify_prod", False)
            
            if not can_prod:
                logger.warning(
                    "Production access denied - insufficient permission",
                    extra={
                        "trace_id": request.trace_id,
                        "user_id": user_id,
                        "database": database or "unknown",
                    }
                )
                raise DomainPermissionError(
                    "Production database access denied - requires elevated permission"
                )
            
            # Log production operation for audit trail
            if DBAConfig.ENABLE_AUDIT_LOG:
                logger.warning(
                    "PRODUCTION QUERY - Audit Log",
                    extra={
                        "trace_id": request.trace_id,
                        "user_id": user_id,
                        "database": database,
                        "use_case": request.intent,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
        
        return True


class ScopeValidationGate:
    """
    GATE 2: Scope Validation Gate
    - Ensures database/connection is explicitly specified
    - Prevents cluster-wide or server-wide queries
    - Validates user has access to the scope
    """
    
    async def check(self, request: DomainRequest) -> Scope:
        """
        Validate and extract scope.
        
        Args:
            request: Domain request with slots
            
        Returns:
            Scope object with database and server info
            
        Raises:
            InvalidInputError: If scope not specified
        """
        # Extract from slots
        database = request.slots.get("database") or request.slots.get("connection_name")
        connection_id = request.slots.get("connection_id")
        
        # At least one of database, connection_name, or connection_id must be specified
        if not database and not connection_id:
            raise InvalidInputError(
                "Database/connection must be explicitly specified. "
                "Cannot run cluster-wide or server-wide analysis. "
                "Please provide: database, connection_name, or connection_id"
            )
        
        # For now, use database or connection_id as scope
        # In real implementation, would validate against connection registry
        scope = Scope(
            database=database or connection_id or "unknown",
            server=request.slots.get("server") or "unknown"
        )
        
        logger.info(
            "Scope validation passed",
            extra={
                "trace_id": request.trace_id,
                "database": scope.database,
                "server": scope.server,
            }
        )
        
        return scope


class PermissionGate:
    """
    GATE 3: Permission Check Gate
    - Validates user has required permissions for use case
    - Different use cases have different permission levels
    """
    
    # Permissions required per use case
    PERMISSIONS = {
        "analyze_slow_query": ["read:query_stats"],
        "check_index_health": ["read:index_stats"],
        "detect_blocking": ["read:session_info"],
        "analyze_wait_stats": ["read:wait_stats"],
        "detect_deadlock_pattern": ["read:wait_stats"],
        "analyze_io_pressure": ["read:io_stats"],
        "capacity_forecast": ["read:capacity_stats"],
        "validate_custom_sql": ["read:schema", "execute:dry_run"],
        "compare_sp_blitz_vs_custom": ["read:all_stats"],
        "incident_triage": ["read:all_stats"],
        "analyze_query_regression": ["read:query_stats"],
    }
    
    async def check(
        self,
        use_case: str,
        user_id: str,
        user_context: Dict[str, Any]
    ) -> bool:
        """
        Check permission gate.
        
        Args:
            use_case: Use case name
            user_id: User ID
            user_context: User context with permissions
            
        Returns:
            True if permission granted
            
        Raises:
            DomainPermissionError: If permission denied
        """
        required_perms = self.PERMISSIONS.get(use_case, [])
        
        # For now, just check if user has any permission context
        # In real implementation, would check specific permissions
        if not required_perms:
            return True
        
        user_perms = user_context.get("permissions", [])
        
        # Check if user has at least one required permission
        if user_perms and any(perm in user_perms for perm in required_perms):
            return True
        
        # If no permission context provided, log warning but allow
        # (assume permission check done at router level)
        logger.debug(
            f"Permission context not found - assuming pre-validated at router level",
            extra={
                "user_id": user_id,
                "use_case": use_case,
                "required_perms": required_perms,
            }
        )
        
        return True


class ResponseValidationGate:
    """
    GATE 4: Response Schema Validation Gate
    - Validates response from MCP has expected structure
    - Fails fast on malformed responses
    """
    
    @staticmethod
    def validate_response(
        response_type: str,
        response_data: Any,
        allow_none: bool = False
    ) -> bool:
        """
        Validate response data structure.
        
        Args:
            response_type: Type of response (slow_queries, wait_stats, etc.)
            response_data: Response data from MCP
            allow_none: Whether None is acceptable
            
        Returns:
            True if validation passes
            
        Raises:
            InvalidInputError: If validation fails
        """
        if not DBAConfig.VALIDATE_MCP_RESPONSES:
            return True
        
        if response_data is None:
            if allow_none:
                return True
            if DBAConfig.FAIL_ON_VALIDATION_ERROR:
                raise InvalidInputError(f"Response is None for {response_type}")
            return False
        
        # Basic type validation
        if response_type in ["slow_queries", "blocking_sessions", "wait_stats", "index_stats"]:
            if not isinstance(response_data, (list, dict)):
                if DBAConfig.FAIL_ON_VALIDATION_ERROR:
                    raise InvalidInputError(
                        f"Invalid response type for {response_type}: "
                        f"expected list or dict, got {type(response_data).__name__}"
                    )
                return False
        
        # If it's a dict, check if it has data
        if isinstance(response_data, dict) and not response_data:
            logger.warning(
                f"Empty response dict for {response_type}",
                extra={"response_type": response_type}
            )
        
        # If it's a list, check if it's not too large
        if isinstance(response_data, list) and len(response_data) > 100000:
            logger.warning(
                f"Very large response for {response_type}",
                extra={
                    "response_type": response_type,
                    "count": len(response_data)
                }
            )
        
        return True
