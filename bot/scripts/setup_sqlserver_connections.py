"""
Script to setup 20 SQL Server connections
Example usage for managing multiple SQL Server connections
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.domain.dba.services.connection_registry import connection_registry
from backend.shared.logger import logger


async def setup_sqlserver_connections():
    """Setup 20 SQL Server connections"""
    
    # Example: 20 SQL Server connections
    servers = [
        {
            "name": f"SQL Server Production {i:02d}",
            "host": f"sql-prod-{i:02d}.example.com",
            "database": "ProductionDB",
            "environment": "production",
            "tags": ["sqlserver", "production", "critical"]
        }
        for i in range(1, 21)
    ]
    
    created_connections = []
    
    for server in servers:
        try:
            # Build connection string
            # Format: mssql+pyodbc://user:password@host:port/database
            connection_string = (
                f"mssql+pyodbc://dbadmin:SecurePass123@{server['host']}:1433/"
                f"{server['database']}?driver=ODBC+Driver+17+for+SQL+Server"
            )
            
            connection = await connection_registry.create_connection(
                name=server["name"],
                db_type="sqlserver",
                connection_string=connection_string,
                description=f"Production SQL Server {server['host']}",
                environment=server["environment"],
                tags=server["tags"],
                created_by="admin@example.com",
                tenant_id="tenant-123"
            )
            
            created_connections.append(connection)
            logger.info(
                f"✅ Created connection: {connection.name} ({connection.connection_id})"
            )
            
        except Exception as e:
            logger.error(
                f"❌ Failed to create connection {server['name']}: {e}",
                exc_info=True
            )
    
    print(f"\n✅ Created {len(created_connections)} connections")
    
    # List all SQL Server connections
    print("\n📋 All SQL Server connections:")
    all_connections = await connection_registry.list_connections(
        db_type="sqlserver",
        tenant_id="tenant-123"
    )
    
    for conn in all_connections:
        print(f"  - {conn.name} ({conn.environment}) - {conn.status}")
    
    return created_connections


async def test_connection_usage():
    """Test using connection in use case"""
    from backend.domain.dba.entry_handler import DBAEntryHandler
    from backend.schemas import DomainRequest
    
    handler = DBAEntryHandler()
    
    # Use connection by name
    request = DomainRequest(
        intent="analyze_slow_query",
        slots={
            "db_type": "sqlserver",
            "connection_name": "SQL Server Production 01",  # Lookup from registry
            "limit": 10,
            "min_duration_ms": 1000
        },
        user_context={
            "user_id": "user-123",
            "tenant_id": "tenant-123"
        }
    )
    
    try:
        response = await handler.handle(request)
        print(f"\n✅ Use case executed: {response.message}")
    except Exception as e:
        print(f"\n❌ Use case failed: {e}")


if __name__ == "__main__":
    print("🚀 Setting up 20 SQL Server connections...\n")
    
    # Run setup
    connections = asyncio.run(setup_sqlserver_connections())
    
    # Test usage
    print("\n🧪 Testing connection usage...")
    asyncio.run(test_connection_usage())
    
    print("\n✅ Done!")

