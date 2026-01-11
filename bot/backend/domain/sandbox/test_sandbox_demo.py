"""
Demo script to test sandbox components locally
"""
import asyncio
from sql_analyzer import SQLAnalyzer
from connection_validator import ConnectionValidator, ConnectionInfo
from query_cost_estimator import QueryCostEstimator


async def main():
    print("=" * 80)
    print("DBA SANDBOX - BACKEND LOGIC DEMO")
    print("=" * 80)

    # ===== SQL ANALYZER TEST =====
    print("\n1. SQL ANALYZER TEST")
    print("-" * 80)
    
    sql_analyzer = SQLAnalyzer()

    test_queries = [
        ("SELECT * FROM users WHERE id = 1", "Simple SELECT"),
        ("' UNION SELECT * FROM passwords--", "SQL Injection Attempt"),
        ("SELECT password, email FROM users", "Sensitive Columns"),
        ("SELECT * FROM sys.tables", "System Tables"),
        ("DELETE FROM users WHERE 1=1", "DELETE without WHERE"),
    ]

    for query, description in test_queries:
        print(f"\nQuery: {description}")
        print(f"SQL: {query}")
        result = sql_analyzer.analyze(query)
        
        print(f"  Injection Safe: {result['sql_injection_safe']}")
        print(f"  Complexity: {result['complexity_level']}")
        print(f"  Sensitive Columns: {result['sensitive_columns_found']}")
        if result['warnings']:
            print(f"  Warnings: {result['warnings']}")
        if result['errors']:
            print(f"  Errors: {result['errors']}")

    # ===== CONNECTION VALIDATOR TEST =====
    print("\n\n2. CONNECTION VALIDATOR TEST")
    print("-" * 80)
    
    validator = ConnectionValidator()

    connections = [
        ConnectionInfo(
            id="dev-1",
            name="DEV_DB",
            db_type="sql_server",
            host="localhost",
            port=1433,
            is_production=False,
            database="development",
        ),
        ConnectionInfo(
            id="prod-1",
            name="PROD_MAIN",
            db_type="sql_server",
            host="prod.example.com",
            port=1433,
            is_production=True,
            database="production",
        ),
    ]

    for conn in connections:
        print(f"\nConnection: {conn.name}")
        validation = await validator.validate(conn)
        
        print(f"  Alive: {validation['is_alive']}")
        print(f"  DB Type: {validation['db_type']}")
        print(f"  Production: {validation['is_production']}")
        print(f"  Permissions: {validation['user_permissions']}")
        print(f"  Duration: {validation['duration_ms']}ms")
        if validation['warning']:
            print(f"  ⚠ Warning: {validation['warning']}")
        if validation['error']:
            print(f"  ✗ Error: {validation['error']}")

    # ===== QUERY COST ESTIMATOR TEST =====
    print("\n\n3. QUERY COST ESTIMATOR TEST")
    print("-" * 80)
    
    cost_estimator = QueryCostEstimator()

    cost_queries = [
        ("SELECT id, name FROM users WHERE id = 1", "Simple lookup"),
        ("SELECT * FROM transactions", "Full table scan"),
        ("SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id", "With JOIN"),
        ("SELECT DISTINCT category FROM products ORDER BY category", "With DISTINCT and ORDER BY"),
    ]

    for query, description in cost_queries:
        print(f"\nQuery: {description}")
        print(f"SQL: {query}")
        cost = cost_estimator.estimate(query)
        
        print(f"  Estimated Rows: {cost['estimated_rows']:,}")
        print(f"  Estimated Duration: {cost['estimated_duration_ms']}ms ({cost['duration_category']})")
        print(f"  Risk Level: {cost['risk_level']}")
        print(f"  Memory: {cost['memory_mb']:.1f}MB")
        if cost['optimization_tips']:
            print(f"  💡 Tips:")
            for tip in cost['optimization_tips'][:2]:
                print(f"     - {tip}")
        if cost['warnings']:
            print(f"  ⚠ Warnings:")
            for warning in cost['warnings'][:2]:
                print(f"     - {warning}")

    print("\n" + "=" * 80)
    print("DEMO COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
