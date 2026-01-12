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


class ConnectionInfoRequest(BaseModel):
    db_type: str
    connection_string: Optional[str] = None


class MCPResponse(BaseModel):
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


def get_connection_string(
    db_type: str,
    provided: Optional[str]
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
    """
    Execute custom query.
    
    This is the main endpoint used by backend execution flow.
    Backend sends queries from dba_query_templates table (ExecutionPlan).
    """
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
        await adapter.connect()
        info = await adapter.get_connection_info()
        
        return MCPResponse(data=info)
    except Exception as e:
        return MCPResponse(
            data=None,
            error={"message": str(e), "type": type(e).__name__}
        )
    finally:
        if adapter:
            await adapter.disconnect()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mcp-db-server"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
