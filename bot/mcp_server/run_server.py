"""
Run MCP DB Server
"""
import os
import uvicorn
from .main import app

if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8387))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    
    print(f"Starting MCP DB Server on {host}:{port}")
    print(f"MCP_DB_SERVER_URL=http://{host}:{port}")
    
    # Use import string for reload to work properly
    if os.getenv("ENVIRONMENT", "development") == "development":
        uvicorn.run(
            "mcp_server.main:app",
            host=host,
            port=port,
            log_level="info",
            reload=True
        )
    else:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            reload=False
        )

