#!/bin/bash
# Start MCP DB Server
# Usage: ./scripts/start_mcp_server.sh

cd "$(dirname "$0")/.."

echo "🚀 Starting MCP DB Server..."
echo ""

# Check if port 8387 is already in use
if lsof -Pi :8387 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8387 is already in use"
    echo "   MCP Server might already be running"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set environment variables
export MCP_SERVER_PORT=${MCP_SERVER_PORT:-8387}
export MCP_SERVER_HOST=${MCP_SERVER_HOST:-0.0.0.0}

echo "📋 Configuration:"
echo "   Host: $MCP_SERVER_HOST"
echo "   Port: $MCP_SERVER_PORT"
echo "   URL: http://$MCP_SERVER_HOST:$MCP_SERVER_PORT"
echo ""

# Start server
python -m mcp_server.run_server

