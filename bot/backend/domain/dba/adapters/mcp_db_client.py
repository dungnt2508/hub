"""
MCP DB Client Implementation
"""
import os
import httpx
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ..ports.mcp_client import IMCPDBClient, DatabaseType
from ..services.connection_registry import ConnectionRegistry
from ....shared.logger import logger
from ....shared.exceptions import ExternalServiceError


class MCPDBClient(IMCPDBClient):
    """MCP DB Client implementation using MCP protocol"""
    
    def __init__(
        self,
        mcp_server_url: Optional[str] = None,
        timeout: float = 30.0,
        connection_registry: Optional[ConnectionRegistry] = None
    ):
        """
        Initialize MCP DB Client.
        
        Args:
            mcp_server_url: MCP server URL (defaults to env var MCP_DB_SERVER_URL)
            timeout: Request timeout in seconds
            connection_registry: Connection registry for looking up connections
        """
        self.mcp_server_url = mcp_server_url or os.getenv(
            "MCP_DB_SERVER_URL",
            "http://localhost:8387"
        )
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.connection_registry = connection_registry or ConnectionRegistry()
        logger.info(f"MCP DB Client initialized with server: {self.mcp_server_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def _call_mcp_server(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        retry_on_error: bool = True
    ) -> Dict[str, Any]:
        """
        Call MCP server endpoint.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            payload: Request payload
            retry_on_error: Whether to retry on error (default: True)
            
        Returns:
            Response data as dictionary
            
        Raises:
            ExternalServiceError: If request fails
        """
        # Use retry decorator only if retry_on_error is True
        if retry_on_error:
            return await self._call_mcp_server_with_retry(method, endpoint, payload)
        else:
            return await self._call_mcp_server_no_retry(method, endpoint, payload)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _call_mcp_server_with_retry(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call MCP server with retry logic"""
        return await self._call_mcp_server_no_retry(method, endpoint, payload)
    
    async def _call_mcp_server_no_retry(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call MCP server endpoint without retry.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            payload: Request payload
            
        Returns:
            Response data as dictionary
            
        Raises:
            ExternalServiceError: If request fails
        """
        url = f"{self.mcp_server_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=payload)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                result = response.json()
            except Exception as e:
                logger.error(
                    f"Failed to parse MCP server JSON response: {e}, response text: {response.text[:200]}",
                    extra={"url": url, "method": method}
                )
                raise ExternalServiceError(f"MCP server returned invalid JSON: {e}")
            
            # Check if result is None or empty
            if result is None:
                logger.error(
                    f"MCP server returned None response, status: {response.status_code}, text: {response.text[:200]}",
                    extra={"url": url, "method": method}
                )
                raise ExternalServiceError("MCP server returned empty response")
            
            # Check for MCP protocol errors
            # Only treat as error if error field exists AND is not None
            if isinstance(result, dict) and result.get("error") is not None:
                error_obj = result.get("error")
                
                # Handle different error formats
                if isinstance(error_obj, dict):
                    error_msg = error_obj.get("message", "Unknown MCP error")
                    if not error_msg or error_msg == "None" or str(error_msg).lower() == "none":
                        error_msg = f"MCP server error: {error_obj.get('type', 'UnknownError')}"
                else:
                    error_msg = str(error_obj)
                    if error_msg == "None" or error_msg.lower() == "none":
                        error_msg = "Unknown MCP error (error message is None)"
                
                # Log connection test failures as debug, others as error
                if "/connection-info" in endpoint:
                    logger.debug(f"MCP server connection test error: {error_msg}, full result: {result}")
                else:
                    logger.error(f"MCP server error: {error_msg}, full result: {result}")
                raise ExternalServiceError(f"MCP server error: {error_msg}")
            
            # Return data if available, otherwise return the whole result
            if isinstance(result, dict):
                return result.get("data", result)
            return result
            
        except httpx.HTTPStatusError as e:
            # Log connection test failures as debug, others as error
            if "/connection-info" in endpoint:
                logger.debug(
                    f"MCP server HTTP error during connection test: {e.response.status_code} - {e.response.text}",
                    extra={"url": url, "method": method}
                )
            else:
                logger.error(
                    f"MCP server HTTP error: {e.response.status_code} - {e.response.text}",
                    extra={"url": url, "method": method}
                )
            raise ExternalServiceError(
                f"MCP server returned {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            logger.error(
                f"MCP server request error: {e}",
                extra={"url": url, "method": method}
            )
            raise ExternalServiceError(f"Failed to connect to MCP server: {e}") from e
        except ExternalServiceError:
            # Re-raise ExternalServiceError without additional logging (already logged above)
            raise
        except Exception as e:
            # Only log as error if it's not a connection test failure
            # Connection test failures are expected and should be handled gracefully
            if "/connection-info" in endpoint:
                logger.debug(
                    f"MCP server error during connection test: {e}",
                    extra={"url": url, "method": method}
                )
            else:
                logger.error(
                    f"Unexpected error calling MCP server: {e}",
                    extra={"url": url, "method": method},
                    exc_info=True
                )
            raise ExternalServiceError(f"Unexpected error: {e}") from e
    
    async def execute_query(
        self,
        query: Optional[str] = None,
        connection_id: Optional[str] = None,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        db_type: Optional[str] = None,
        timeout_seconds: int = 300,
        params: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        # Support old signature for backward compatibility
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Execute query via MCP server.
        
        Supports both new and old signatures for backward compatibility:
        - New: execute_query(query=..., connection_id=..., db_type=...)
        - Old: execute_query(db_type=..., query=..., connection_string=...)
        """
        # Handle old signature where db_type is passed first positionally or as kwarg
        if query is None and 'db_type' in kwargs:
            # Old-style call: execute_query(db_type=..., query=..., connection_string=...)
            db_type_kwarg = db_type or kwargs.get('db_type')
            if isinstance(db_type_kwarg, DatabaseType):
                db_type = db_type_kwarg.value
            elif isinstance(db_type_kwarg, str):
                db_type = db_type_kwarg
            
            # Get query from kwargs if not provided
            query = kwargs.get('query')
            connection_string = connection_string or kwargs.get('connection_string')
        
        if not query:
            raise ValueError("query parameter is required")
        
        logger.debug(
            f"Executing query",
            extra={
                "query_length": len(query),
                "timeout_seconds": timeout_seconds,
                "has_connection_id": bool(connection_id),
                "has_connection_string": bool(connection_string),
                "db_type": db_type
            }
        )
        
        # Resolve connection string if not provided but connection_id is
        resolved_conn_string = connection_string
        if not resolved_conn_string and (connection_id or connection_name):
            try:
                resolved_conn_string = await self._resolve_connection_string(
                    connection_string=connection_string,
                    connection_name=connection_name,
                    connection_id=connection_id,
                    tenant_id=tenant_id
                )
                if resolved_conn_string:
                    logger.debug(
                        f"Resolved connection string",
                        extra={"connection_id": connection_id, "connection_name": connection_name}
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to resolve connection string: {e}",
                    extra={"connection_id": connection_id, "connection_name": connection_name}
                )
        
        # Build payload
        payload = {
            "query": query,
            "params": params or {},
            "timeout_seconds": timeout_seconds,
        }
        
        # Add connection info - prefer resolved connection string
        if resolved_conn_string:
            payload["connection_string"] = resolved_conn_string
        elif connection_string:
            payload["connection_string"] = connection_string
        elif connection_id:
            payload["connection_id"] = str(connection_id)
        elif connection_name:
            payload["connection_name"] = connection_name
        
        # Add db_type if provided
        if db_type:
            # Handle DatabaseType enum
            if hasattr(db_type, 'value'):
                payload["db_type"] = db_type.value
            else:
                payload["db_type"] = str(db_type)
        
        result = await self._call_mcp_server("POST", "/execute", payload)
        return result if isinstance(result, list) else [result]
    
    async def _resolve_connection_string(
        self,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """Resolve connection string from registry if not provided"""
        if connection_string:
            return connection_string
        
        if connection_name or connection_id:
            return await self.connection_registry.get_connection_string(
                connection_name=connection_name,
                connection_id=connection_id,
                tenant_id=tenant_id
            )
        
        return None
    
    async def get_slow_queries(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 10,
        min_duration_ms: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get slow queries via MCP server"""
        logger.debug(
            f"Getting slow queries from {db_type.value}",
            extra={"db_type": db_type.value, "limit": limit, "min_duration_ms": min_duration_ms}
        )
        
        # Resolve connection string from registry if needed
        resolved_connection_string = await self._resolve_connection_string(
            connection_string=connection_string,
            connection_name=connection_name,
            connection_id=connection_id,
            tenant_id=tenant_id
        )
        
        payload = {
            "db_type": db_type.value,
            "limit": limit,
            "min_duration_ms": min_duration_ms
        }
        
        if resolved_connection_string:
            payload["connection_string"] = resolved_connection_string
        elif connection_name:
            payload["connection_name"] = connection_name
        elif connection_id:
            payload["connection_id"] = connection_id
        
        result = await self._call_mcp_server("POST", "/slow-queries", payload)
        return result if isinstance(result, list) else [result]
    
    async def get_wait_stats(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get wait statistics via MCP server"""
        logger.debug(f"Getting wait stats from {db_type.value}")
        
        resolved_connection_string = await self._resolve_connection_string(
            connection_string=connection_string,
            connection_name=connection_name,
            connection_id=connection_id,
            tenant_id=tenant_id
        )
        
        payload = {"db_type": db_type.value}
        if resolved_connection_string:
            payload["connection_string"] = resolved_connection_string
        elif connection_name:
            payload["connection_name"] = connection_name
        elif connection_id:
            payload["connection_id"] = connection_id
        
        result = await self._call_mcp_server("POST", "/wait-stats", payload)
        return result if isinstance(result, dict) else {"wait_stats": result}
    
    async def get_index_stats(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get index statistics via MCP server"""
        logger.debug(
            f"Getting index stats from {db_type.value}",
            extra={"schema": schema}
        )
        
        resolved_connection_string = await self._resolve_connection_string(
            connection_string=connection_string,
            connection_name=connection_name,
            connection_id=connection_id,
            tenant_id=tenant_id
        )
        
        payload = {"db_type": db_type.value}
        if resolved_connection_string:
            payload["connection_string"] = resolved_connection_string
        elif connection_name:
            payload["connection_name"] = connection_name
        elif connection_id:
            payload["connection_id"] = connection_id
        if schema:
            payload["schema_name"] = schema  # Changed to schema_name to match IndexStatsRequest
        
        result = await self._call_mcp_server("POST", "/index-stats", payload)
        return result if isinstance(result, list) else [result]
    
    async def detect_blocking(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None,
        connection_name: Optional[str] = None,
        connection_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Detect blocking sessions via MCP server"""
        logger.debug(f"Detecting blocking in {db_type.value}")
        
        resolved_connection_string = await self._resolve_connection_string(
            connection_string=connection_string,
            connection_name=connection_name,
            connection_id=connection_id,
            tenant_id=tenant_id
        )
        
        payload = {"db_type": db_type.value}
        if resolved_connection_string:
            payload["connection_string"] = resolved_connection_string
        elif connection_name:
            payload["connection_name"] = connection_name
        elif connection_id:
            payload["connection_id"] = connection_id
        
        result = await self._call_mcp_server("POST", "/blocking", payload)
        return result if isinstance(result, list) else [result]
    
    async def get_connection_info(
        self,
        db_type: DatabaseType,
        connection_string: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get database connection information via MCP server"""
        logger.debug(f"Getting connection info for {db_type.value}")
        
        payload = {"db_type": db_type.value}
        if connection_string:
            payload["connection_string"] = connection_string
        
        try:
            # Don't retry connection test failures - they are expected
            result = await self._call_mcp_server("POST", "/connection-info", payload, retry_on_error=False)
            
            # Check if result contains error (only if error is not None)
            if isinstance(result, dict) and result.get("error") is not None:
                error_info = result.get("error", {})
                if isinstance(error_info, dict):
                    error_msg = error_info.get("message", "Connection test failed")
                    if not error_msg or str(error_msg).lower() == "none":
                        error_msg = f"Connection test failed: {error_info.get('type', 'UnknownError')}"
                else:
                    error_msg = str(error_info)
                    if error_msg.lower() == "none":
                        error_msg = "Connection test failed (error message is None)"
                raise ExternalServiceError(f"MCP Server error: {error_msg}")
            
            return result if isinstance(result, dict) else {"info": result}
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}", exc_info=True)
            raise ExternalServiceError(f"Failed to get connection info: {str(e)}") from e

