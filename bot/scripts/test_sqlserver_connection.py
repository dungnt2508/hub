#!/usr/bin/env python3
"""
Script để test kết nối SQL Server từ container
Usage: 
    python scripts/test_sqlserver_connection.py "sqlserver://sa:password@host.docker.internal:1444?database=master"
    hoặc
    docker exec -it bot_mcp_server python /app/scripts/test_sqlserver_connection.py "sqlserver://sa:password@192.168.11.90:1444?database=master"
"""
import sys
import os
from urllib.parse import urlparse, parse_qs

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_connection(connection_string: str):
    """Test SQL Server connection"""
    print("=" * 60)
    print("Testing SQL Server Connection")
    print("=" * 60)
    print(f"Connection String: {connection_string}")
    print()
    
    # Parse connection string
    if not connection_string.startswith("sqlserver://"):
        print("❌ Connection string must start with 'sqlserver://'")
        return False
    
    conn_str = connection_string.replace("sqlserver://", "http://")
    parsed = urlparse(conn_str)
    query_params = parse_qs(parsed.query)
    
    host = parsed.hostname or "localhost"
    port = parsed.port or 1433
    user = parsed.username
    password = parsed.password
    database = query_params.get("database", [None])[0] or "master"
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    print(f"Database: {database}")
    print()
    
    # Test 1: Check if host is reachable
    print("1. Testing host reachability...")
    import socket
    try:
        socket.create_connection((host, port), timeout=3)
        print(f"   ✅ Host {host}:{port} is reachable")
    except socket.timeout:
        print(f"   ❌ Host {host}:{port} is NOT reachable (timeout)")
        return False
    except socket.error as e:
        print(f"   ❌ Host {host}:{port} is NOT reachable: {e}")
        return False
    
    # Test 2: Test actual SQL Server connection
    print()
    print("2. Testing SQL Server connection...")
    try:
        import pymssql
        
        server = f"{host}:{port}" if port != 1433 else host
        print(f"   Connecting to {server}...")
        
        conn = pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=database,
            timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT DB_NAME(), SYSTEM_USER")
        db_info = cursor.fetchone()
        
        print(f"   ✅ Connection successful!")
        print(f"   SQL Server Version: {version[:80]}...")
        print(f"   Current Database: {db_info[0]}")
        print(f"   Current User: {db_info[1]}")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("✅ Connection test PASSED!")
        print("=" * 60)
        return True
        
    except ImportError:
        print("   ⚠️  pymssql not installed")
        print("   💡 Install with: pip install pymssql")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        print("=" * 60)
        print("❌ Connection test FAILED!")
        print("=" * 60)
        print()
        print("Troubleshooting:")
        print("1. Check if SQL Server is running on host machine")
        print("2. Check if SQL Server allows remote connections")
        print("3. Check firewall settings")
        print("4. Try using IP address instead of hostname:")
        print("   - Windows: ipconfig | findstr IPv4")
        print("   - Linux/Mac: hostname -I")
        print("5. For Windows/Mac Docker Desktop, try: host.docker.internal")
        print("6. For Linux, use host machine IP address")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_sqlserver_connection.py <connection_string>")
        print()
        print("Examples:")
        print('  python test_sqlserver_connection.py "sqlserver://sa:password@host.docker.internal:1444?database=master"')
        print('  python test_sqlserver_connection.py "sqlserver://sa:password@192.168.11.90:1444?database=master"')
        sys.exit(1)
    
    connection_string = sys.argv[1]
    success = test_connection(connection_string)
    sys.exit(0 if success else 1)

