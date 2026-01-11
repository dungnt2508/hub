"""
DBA Domain Use Case Examples

This file demonstrates how to use the DBA domain entry handler
and various use cases for database analysis.
"""

import asyncio
from backend.schemas import DomainRequest, DomainResponse
from backend.domain.dba import DBAEntryHandler


async def example_analyze_slow_query():
    """Example: Analyze slow queries"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="analyze_slow_query",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "postgresql",
            "connection_name": "prod_db",
            "limit": 20,
            "min_duration_ms": 500,
        },
    )
    
    response = await handler.handle(request)
    print(f"Slow Query Analysis: {response.message}")
    print(f"Found {response.data.get('count')} slow queries")


async def example_check_index_health():
    """Example: Check index health"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="check_index_health",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "mysql",
            "connection_name": "mysql_prod",
            "schema": "myapp_db",
        },
    )
    
    response = await handler.handle(request)
    print(f"Index Health Check: {response.message}")
    print(f"Total indexes: {response.data.get('total_indexes')}")
    print(f"Unhealthy indexes: {response.data.get('unhealthy_count')}")


async def example_detect_blocking():
    """Example: Detect blocking sessions"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="detect_blocking",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "sqlserver",
            "connection_name": "sqlserver_prod",
        },
    )
    
    response = await handler.handle(request)
    print(f"Blocking Detection: {response.message}")
    print(f"Blocking sessions: {response.data.get('blocking_count')}")
    print(f"Critical blocking: {response.data.get('critical_count')}")


async def example_analyze_wait_stats():
    """Example: Analyze wait statistics"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="analyze_wait_stats",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "sqlserver",
            "connection_string": "server=localhost;database=mydb",
        },
    )
    
    response = await handler.handle(request)
    print(f"Wait Stats Analysis: {response.message}")
    print(f"Top wait events: {response.data.get('top_wait_events')}")


async def example_analyze_query_regression():
    """Example: Analyze query regression"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="analyze_query_regression",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "postgresql",
            "connection_name": "prod_db",
            "baseline_period_days": 7,
            "regression_threshold_percent": 20,
        },
    )
    
    response = await handler.handle(request)
    print(f"Query Regression Analysis: {response.message}")
    print(f"Regressed queries: {response.data.get('regression_count')}")


async def example_capacity_forecast():
    """Example: Forecast capacity"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="capacity_forecast",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "mysql",
            "connection_name": "mysql_prod",
            "forecast_days": 30,
        },
    )
    
    response = await handler.handle(request)
    print(f"Capacity Forecast: {response.message}")
    print(f"Critical forecasts: {len(response.data.get('critical_forecasts', []))}")
    print(f"Warning forecasts: {len(response.data.get('warning_forecasts', []))}")


async def example_validate_custom_sql():
    """Example: Validate custom SQL"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="validate_custom_sql",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "postgresql",
            "sql_query": "SELECT * FROM users WHERE age > 18",
            "check_performance": True,
        },
    )
    
    response = await handler.handle(request)
    print(f"SQL Validation: {response.message}")
    print(f"Validation status: {response.data.get('validation_status')}")
    print(f"Issues found: {len(response.data.get('issues', []))}")


async def example_incident_triage():
    """Example: Incident triage"""
    handler = DBAEntryHandler()
    
    request = DomainRequest(
        intent="incident_triage",
        user_context={
            "user_id": "user123",
            "tenant_id": "tenant456",
        },
        slots={
            "db_type": "sqlserver",
            "incident_description": (
                "Database is experiencing high CPU usage, queries are running slowly, "
                "and some connections are blocked for extended periods."
            ),
        },
    )
    
    response = await handler.handle(request)
    incident = response.data.get('incident')
    print(f"Incident Triage: {response.message}")
    print(f"Incident Type: {incident.get('incident_type')}")
    print(f"Severity: {incident.get('severity')}")
    print(f"Recommendations: {response.data.get('recommendations')}")


async def main():
    """Run all examples"""
    print("=" * 80)
    print("DBA Domain Use Case Examples")
    print("=" * 80)
    
    examples = [
        ("Analyze Slow Query", example_analyze_slow_query),
        ("Check Index Health", example_check_index_health),
        ("Detect Blocking", example_detect_blocking),
        ("Analyze Wait Stats", example_analyze_wait_stats),
        ("Query Regression Analysis", example_analyze_query_regression),
        ("Capacity Forecast", example_capacity_forecast),
        ("Validate Custom SQL", example_validate_custom_sql),
        ("Incident Triage", example_incident_triage),
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*80}")
        print(f"Example: {name}")
        print(f"{'='*80}")
        try:
            await example_func()
        except Exception as e:
            print(f"Error: {e}")
            # In real scenario, would log error but continue


if __name__ == "__main__":
    asyncio.run(main())
