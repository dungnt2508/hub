"""
MCP DB Server - Main Entry Point
FastAPI server implementing MCP protocol for database operations
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import uvicorn

from .database_adapters import (
    get_adapter,
    DatabaseAdapter,
    DatabaseType,
)
from .query_templates import QUERY_TEMPLATES

app = FastAPI(
    title="MCP DB Server",
    description="MCP Server for Database Operations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ExecuteQueryRequest(BaseModel):
    db_type: str
    query: str
    connection_string: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class SlowQueriesRequest(BaseModel):
    db_type: str
    connection_string: Optional[str] = None
    limit: int = 10
    min_duration_ms: int = 1000


class WaitStatsRequest(BaseModel):
    db_type: str
    connection_string: Optional[str] = None


class IndexStatsRequest(BaseModel):
    db_type: str
    connection_string: Optional[str] = None
    schema_name: Optional[str] = None  # Renamed from 'schema' to avoid shadowing BaseModel attribute


class BlockingRequest(BaseModel):
    db_type: str
    connection_string: Optional[str] = None


class ConnectionInfoRequest(BaseModel):
    db_type: str
    connection_string: Optional[str] = None


class MCPResponse(BaseModel):
    data: Any
    error: Optional[Dict[str, Any]] = None


# Helper function to get connection string
def get_connection_string(
    db_type: str,
    provided: Optional[str] = None
) -> str:
    """Get connection string from env or provided"""
    if provided:
        return provided
    
    # Try environment variables
    env_key = f"DBA_DEFAULT_{db_type.upper()}_URL"
    return os.getenv(env_key, "")


# API Endpoints
@app.post("/execute", response_model=MCPResponse)
async def execute_query(request: ExecuteQueryRequest):
    """Execute custom query"""
    try:
        db_type = DatabaseType(request.db_type.lower())
        connection_string = get_connection_string(request.db_type, request.connection_string)
        
        if not connection_string:
            raise HTTPException(
                status_code=400,
                detail="Connection string is required"
            )
        
        adapter = get_adapter(db_type, connection_string)
        result = await adapter.execute_query(
            request.query,
            request.params or {}
        )
        
        return MCPResponse(data=result)
    except Exception as e:
        return MCPResponse(
            data=None,
            error={"message": str(e), "type": type(e).__name__}
        )


@app.post("/slow-queries", response_model=MCPResponse)
async def get_slow_queries(request: SlowQueriesRequest):
    """Get slow queries"""
    try:
        db_type = DatabaseType(request.db_type.lower())
        connection_string = get_connection_string(request.db_type, request.connection_string)
        
        if not connection_string:
            raise HTTPException(
                status_code=400,
                detail="Connection string is required"
            )
        
        adapter = get_adapter(db_type, connection_string)
        
        # Get query template
        templates = QUERY_TEMPLATES.get(db_type, {})
        query_template = templates.get("slow_queries")
        
        if not query_template:
            raise HTTPException(
                status_code=400,
                detail=f"Slow queries query not implemented for {db_type.value}"
            )
        
        # Execute query with parameters
        result = await adapter.execute_query(
            query_template,
            {
                "limit": request.limit,
                "min_duration_ms": request.min_duration_ms
            }
        )
        
        return MCPResponse(data=result)
    except Exception as e:
        return MCPResponse(
            data=None,
            error={"message": str(e), "type": type(e).__name__}
        )


@app.post("/wait-stats", response_model=MCPResponse)
async def get_wait_stats(request: WaitStatsRequest):
    """Get wait statistics"""
    try:
        db_type = DatabaseType(request.db_type.lower())
        connection_string = get_connection_string(request.db_type, request.connection_string)
        
        if not connection_string:
            raise HTTPException(
                status_code=400,
                detail="Connection string is required"
            )
        
        adapter = get_adapter(db_type, connection_string)
        
        templates = QUERY_TEMPLATES.get(db_type, {})
        query_template = templates.get("wait_stats")
        
        if not query_template:
            raise HTTPException(
                status_code=400,
                detail=f"Wait stats query not implemented for {db_type.value}"
            )
        
        result = await adapter.execute_query(query_template, {})
        
        return MCPResponse(data=result)
    except Exception as e:
        return MCPResponse(
            data=None,
            error={"message": str(e), "type": type(e).__name__}
        )


@app.post("/index-stats", response_model=MCPResponse)
async def get_index_stats(request: IndexStatsRequest):
    """Get index statistics"""
    try:
        db_type = DatabaseType(request.db_type.lower())
        connection_string = get_connection_string(request.db_type, request.connection_string)
        
        if not connection_string:
            raise HTTPException(
                status_code=400,
                detail="Connection string is required"
            )
        
        adapter = get_adapter(db_type, connection_string)
        
        templates = QUERY_TEMPLATES.get(db_type, {})
        query_template = templates.get("index_health")
        
        if not query_template:
            raise HTTPException(
                status_code=400,
                detail=f"Index stats query not implemented for {db_type.value}"
            )
        
        result = await adapter.execute_query(
            query_template,
            {"schema": request.schema_name} if request.schema_name else {}
        )
        
        return MCPResponse(data=result)
    except Exception as e:
        return MCPResponse(
            data=None,
            error={"message": str(e), "type": type(e).__name__}
        )


@app.post("/blocking", response_model=MCPResponse)
async def detect_blocking(request: BlockingRequest):
    """Detect blocking sessions"""
    try:
        db_type = DatabaseType(request.db_type.lower())
        connection_string = get_connection_string(request.db_type, request.connection_string)
        
        if not connection_string:
            raise HTTPException(
                status_code=400,
                detail="Connection string is required"
            )
        
        adapter = get_adapter(db_type, connection_string)
        
        templates = QUERY_TEMPLATES.get(db_type, {})
        query_template = templates.get("blocking")
        
        if not query_template:
            raise HTTPException(
                status_code=400,
                detail=f"Blocking detection query not implemented for {db_type.value}"
            )
        
        result = await adapter.execute_query(query_template, {})
        
        return MCPResponse(data=result)
    except Exception as e:
        return MCPResponse(
            data=None,
            error={"message": str(e), "type": type(e).__name__}
        )


@app.post("/connection-info", response_model=MCPResponse)
async def get_connection_info(request: ConnectionInfoRequest):
    """Get database connection information"""
    adapter = None
    try:
        db_type = DatabaseType(request.db_type.lower())
        connection_string = get_connection_string(request.db_type, request.connection_string)
        
        if not connection_string:
            raise HTTPException(
                status_code=400,
                detail="Connection string is required"
            )
        
        adapter = get_adapter(db_type, connection_string)
        info = await adapter.get_connection_info()
        
        # Close connection after use
        await adapter.disconnect()
        
        return MCPResponse(data=info)
    except Exception as e:
        # Ensure connection is closed on error
        if adapter:
            try:
                await adapter.disconnect()
            except:
                pass
        
        return MCPResponse(
            data=None,
            error={"message": str(e), "type": type(e).__name__}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-db-server"}


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8387))
    uvicorn.run(app, host="0.0.0.0", port=port)

