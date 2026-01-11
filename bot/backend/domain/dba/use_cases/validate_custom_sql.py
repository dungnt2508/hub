"""
Validate Custom SQL Use Case
"""
from typing import Optional, Dict, Any

from ....schemas import DomainRequest, DomainResponse, DomainResult
from ....shared.exceptions import InvalidInputError, DomainError
from ....shared.logger import logger
from .base_use_case import BaseUseCase
from ...dba.ports.mcp_client import IMCPDBClient, DatabaseType


class ValidateCustomSQLUseCase(BaseUseCase):
    """Use case for validating custom SQL queries"""
    
    def __init__(self, mcp_client: IMCPDBClient):
        """
        Initialize use case.
        
        Args:
            mcp_client: MCP DB client (required, injected)
        """
        super().__init__()
        if mcp_client is None:
            raise ValueError("MCP client is required for ValidateCustomSQLUseCase")
        self.mcp_client = mcp_client
    
    async def _execute_impl(self, request: DomainRequest, db_type: DatabaseType) -> Dict[str, Any]:
        """
        Execute SQL validation (DIAGNOSTIC ONLY).
        
        Args:
            request: Domain request with slots:
                - sql_query: SQL query to validate (required)
                - check_performance: Whether to check performance (default: True)
                - connection_string: Database connection string (optional)
            db_type: Validated database type
            
        Returns:
            Response dict with validation results
            
        Raises:
            InvalidInputError: If sql_query is missing
            DomainError: If validation fails
        """
        try:
            # Extract slots
            sql_query = request.slots.get("sql_query")
            check_performance = request.slots.get("check_performance", True)
            connection_string = request.slots.get("connection_string")
            
            # Validate required slots
            missing = self.validate_slots(request, ["sql_query"])
            if missing:
                raise InvalidInputError(f"Missing required slots: {', '.join(missing)}")
            
            # Perform static validation ONLY (no modification of query)
            static_issues = self._validate_sql_syntax(sql_query, db_type)
            
            # Perform dynamic validation if connection available
            # IMPORTANT: Execute original query, no modifications
            dynamic_issues = []
            if connection_string or request.slots.get("connection_name"):
                try:
                    dynamic_issues = await self._validate_sql_execution_safe(
                        db_type, sql_query, connection_string, check_performance
                    )
                except Exception as e:
                    logger.debug(f"Could not perform dynamic validation: {e}")
                    dynamic_issues = [{
                        "severity": "warning",
                        "type": "dynamic_validation_failed",
                        "message": f"Dynamic validation skipped: {str(e)}",
                    }]
            
            # Combine issues
            all_issues = static_issues + dynamic_issues
            has_errors = any(issue.get("severity") == "error" for issue in all_issues)
            has_warnings = any(issue.get("severity") == "warning" for issue in all_issues)
            
            validation_status = "error" if has_errors else \
                               "warning" if has_warnings else "valid"
            
            message = (
                f"SQL validation cho {db_type.value}: "
                f"Status = {validation_status.upper()}, "
                f"{len(all_issues)} issues found"
                if all_issues
                else f"SQL query hợp lệ cho {db_type.value}"
            )
            
            return {
                "data": {
                    "query": sql_query,
                    "validation_status": validation_status,
                    "issues": all_issues,
                    "db_type": db_type.value,
                    "static_valid": len(static_issues) == 0,
                    "dynamic_valid": len(dynamic_issues) == 0,
                    "is_original_query": True,  # ← Assurance that query was NOT modified
                },
                "message": message,
            }
            
        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(
                f"Error validating SQL: {e}",
                extra={"trace_id": request.trace_id},
                exc_info=True
            )
            raise DomainError(f"Failed to validate SQL: {e}") from e
    
    def _validate_required_slots(self, request: DomainRequest) -> None:
        """Override to add sql_query to required slots"""
        required_slots = ["db_type", "sql_query"]
        missing = self.validate_slots(request, required_slots)
        if missing:
            raise InvalidInputError(f"Missing required slots: {', '.join(missing)}")
    
    @staticmethod
    def _validate_sql_syntax(sql_query: str, db_type: DatabaseType) -> list:
        """Validate SQL syntax (simplified static checks)"""
        issues = []
        
        # Check for basic SQL issues
        query_upper = sql_query.upper().strip()
        
        # Check for SELECT without FROM
        if query_upper.startswith("SELECT") and "FROM" not in query_upper:
            # SELECT without FROM is valid in some databases
            if db_type != DatabaseType.MYSQL and "SELECT 1" not in query_upper:
                issues.append({
                    "severity": "warning",
                    "type": "missing_from",
                    "message": "SELECT statement should have FROM clause",
                })
        
        # Check for potential SQL injection patterns
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
        for keyword in dangerous_keywords:
            if query_upper.startswith(keyword):
                issues.append({
                    "severity": "warning",
                    "type": "dangerous_operation",
                    "message": f"Query contains {keyword} operation - ensure this is intentional",
                })
        
        # Check for common mistakes
        if "SELECT *" in query_upper and "WHERE" not in query_upper:
            issues.append({
                "severity": "warning",
                "type": "select_all",
                "message": "SELECT * without WHERE clause may return too many rows",
            })
        
        # Check for missing alias in joins
        if "JOIN" in query_upper and query_upper.count(",") > query_upper.count("JOIN"):
            issues.append({
                "severity": "info",
                "type": "style",
                "message": "Consider using explicit JOIN syntax instead of comma-separated tables",
            })
        
        return issues
    
    async def _validate_sql_execution_safe(
        self,
        db_type: DatabaseType,
        sql_query: str,
        connection_string: Optional[str],
        check_performance: bool
    ) -> list:
        """
        Validate SQL by attempting execution in a SAFE manner.
        
        IMPORTANT: This is DIAGNOSTIC ONLY.
        - Does NOT modify the original query
        - Only validates that syntax is correct
        - For SELECT queries, may add transaction wrapper for safety
        - NEVER changes the actual SQL being validated
        
        Args:
            db_type: Database type
            sql_query: Original SQL query (will not be modified)
            connection_string: Connection string
            check_performance: Whether to check performance impact
            
        Returns:
            List of issues found (if any)
        """
        issues = []
        
        try:
            # RULE 1: Only SELECT queries can be executed for validation
            query_upper = sql_query.upper().strip()
            if not query_upper.startswith("SELECT"):
                issues.append({
                    "severity": "info",
                    "type": "non_select",
                    "message": "Dynamic validation only available for SELECT queries",
                })
                return issues
            
            # RULE 2: Execute original query WITHOUT modification
            # In production, this would be wrapped in transaction + rollback
            try:
                result = await self.mcp_client.execute_query(
                    db_type=db_type,
                    query=sql_query,  # ← ORIGINAL QUERY, no modification
                    connection_string=connection_string
                )
                
                # If execution successful, optionally check result size
                if check_performance and isinstance(result, list):
                    if len(result) > 10000:
                        issues.append({
                            "severity": "warning",
                            "type": "performance",
                            "message": (
                                f"Query returns {len(result)} rows - large result set. "
                                "Consider adding WHERE clause or LIMIT for production use."
                            ),
                        })
                
            except Exception as exec_error:
                issues.append({
                    "severity": "error",
                    "type": "execution",
                    "message": f"Query execution failed: {str(exec_error)}",
                })
        
        except Exception as e:
            issues.append({
                "severity": "error",
                "type": "validation_error",
                "message": f"Validation error: {str(e)}",
            })
        
        return issues
