#!/bin/bash
# Script để test kết nối SQL Server từ container
# Usage: docker exec -it bot_mcp_server bash /app/scripts/test_sqlserver_connection.sh <connection_string>

set -e

CONNECTION_STRING="${1:-sqlserver://sa:abcd1234@host.docker.internal:1444?database=master}"

echo "=========================================="
echo "Testing SQL Server Connection"
echo "=========================================="
echo "Connection String: $CONNECTION_STRING"
echo ""

# Test 1: Check if we can resolve hostname
echo "1. Testing hostname resolution..."
if echo "$CONNECTION_STRING" | grep -q "host.docker.internal"; then
    echo "   Hostname: host.docker.internal"
    if ping -c 1 host.docker.internal > /dev/null 2>&1; then
        echo "   ✅ host.docker.internal is reachable"
    else
        echo "   ❌ host.docker.internal is NOT reachable"
        echo "   💡 Try using IP address instead"
    fi
elif echo "$CONNECTION_STRING" | grep -qE "@[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"; then
    IP=$(echo "$CONNECTION_STRING" | grep -oE "@[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | tr -d '@')
    echo "   IP Address: $IP"
    if ping -c 1 "$IP" > /dev/null 2>&1; then
        echo "   ✅ IP $IP is reachable"
    else
        echo "   ❌ IP $IP is NOT reachable"
    fi
fi

# Test 2: Check if port is accessible
echo ""
echo "2. Testing port accessibility..."
PORT=$(echo "$CONNECTION_STRING" | grep -oE ":[0-9]+" | head -1 | tr -d ':')
if [ -z "$PORT" ]; then
    PORT=1433  # Default SQL Server port
fi
echo "   Port: $PORT"

HOST=$(echo "$CONNECTION_STRING" | grep -oE "@[^:]+" | tr -d '@')
if [ -z "$HOST" ]; then
    HOST="localhost"
fi

if timeout 3 bash -c "echo > /dev/tcp/$HOST/$PORT" 2>/dev/null; then
    echo "   ✅ Port $PORT on $HOST is accessible"
else
    echo "   ❌ Port $PORT on $HOST is NOT accessible"
    echo "   💡 Make sure SQL Server is running and firewall allows connections"
fi

# Test 3: Test actual connection via Python
echo ""
echo "3. Testing actual SQL Server connection..."
python3 << EOF
import sys
import asyncio
from urllib.parse import urlparse, parse_qs

connection_string = "$CONNECTION_STRING"

# Parse connection string
if connection_string.startswith("sqlserver://"):
    conn_str = connection_string.replace("sqlserver://", "http://")
    parsed = urlparse(conn_str)
    query_params = parse_qs(parsed.query)
    
    host = parsed.hostname or "localhost"
    port = parsed.port or 1433
    user = parsed.username
    password = parsed.password
    database = query_params.get("database", [None])[0] or "master"
    
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   User: {user}")
    print(f"   Database: {database}")
    
    # Try to connect using pymssql
    try:
        import pymssql
        print("   Attempting connection...")
        conn = pymssql.connect(
            server=f"{host}:{port}" if port != 1433 else host,
            user=user,
            password=password,
            database=database,
            timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"   ✅ Connection successful!")
        print(f"   SQL Server Version: {version[:50]}...")
        cursor.close()
        conn.close()
    except ImportError:
        print("   ⚠️  pymssql not installed, skipping connection test")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        sys.exit(1)
EOF

echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="

