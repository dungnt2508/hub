"""
DBA Use Case Metadata Definitions

All use case metadata is defined here - single source of truth.
"""
from .use_case_metadata import dba_use_case_metadata_registry


def register_all_use_case_metadata():
    """
    Register all DBA use case metadata.
    
    This function should be called during module initialization.
    """
    # 1. Analyze Slow Query
    dba_use_case_metadata_registry.register(
        use_case_id="analyze_slow_query",
        name="Analyze Slow Queries",
        description="Find slow running queries on database",
        icon="📊",
        required_slots=["db_type"],
        optional_slots=["connection_id", "limit", "min_duration_ms"],
        source_allowed=["OPERATION"],
        playbook_name="QUERY_PERFORMANCE",
    )
    
    # 2. Check Index Health
    dba_use_case_metadata_registry.register(
        use_case_id="check_index_health",
        name="Check Index Health",
        description="Check database index health and fragmentation",
        icon="🔍",
        required_slots=["db_type"],
        optional_slots=["connection_id", "schema"],
        source_allowed=["OPERATION"],
        playbook_name="INDEX_HEALTH",
    )
    
    # 3. Detect Blocking
    dba_use_case_metadata_registry.register(
        use_case_id="detect_blocking",
        name="Detect Blocking",
        description="Find blocking and locked transactions",
        icon="🚫",
        required_slots=["db_type"],
        optional_slots=["connection_id"],
        source_allowed=["OPERATION"],
        playbook_name="BLOCKING_ANALYSIS",
    )
    
    # 4. Analyze Wait Stats
    dba_use_case_metadata_registry.register(
        use_case_id="analyze_wait_stats",
        name="Analyze Wait Statistics",
        description="Analyze database wait events and bottlenecks",
        icon="⏳",
        required_slots=["db_type"],
        optional_slots=["connection_id"],
        source_allowed=["OPERATION"],
        playbook_name="WAIT_STATISTICS",
    )
    
    # 5. Detect Deadlock Pattern
    dba_use_case_metadata_registry.register(
        use_case_id="detect_deadlock_pattern",
        name="Detect Deadlocks",
        description="Detect deadlock patterns in transaction logs",
        icon="💀",
        required_slots=["db_type"],
        optional_slots=["connection_id", "time_window_hours"],
        source_allowed=["OPERATION"],
        playbook_name="DEADLOCK_DETECTION",
    )
    
    # 6. Analyze I/O Pressure
    dba_use_case_metadata_registry.register(
        use_case_id="analyze_io_pressure",
        name="Analyze I/O Pressure",
        description="Analyze disk I/O utilization and bottlenecks",
        icon="📈",
        required_slots=["db_type"],
        optional_slots=["connection_id"],
        source_allowed=["OPERATION"],
        playbook_name="IO_PRESSURE",
    )
    
    # 7. Capacity Forecast
    dba_use_case_metadata_registry.register(
        use_case_id="capacity_forecast",
        name="Capacity Forecast",
        description="Forecast database capacity and growth",
        icon="📉",
        required_slots=["db_type"],
        optional_slots=["connection_id", "forecast_days"],
        source_allowed=["OPERATION"],
        playbook_name="CAPACITY_PLANNING",
    )
    
    # 8. Validate Custom SQL
    dba_use_case_metadata_registry.register(
        use_case_id="validate_custom_sql",
        name="Validate Custom SQL",
        description="Validate custom SQL for syntax and safety",
        icon="✅",
        required_slots=["db_type", "sql_query"],
        optional_slots=["connection_id"],
        source_allowed=["OPERATION"],
        playbook_name=None,  # No playbook - uses custom SQL
    )
    
    # 9. Analyze Query Regression
    dba_use_case_metadata_registry.register(
        use_case_id="analyze_query_regression",
        name="Detect Query Regression",
        description="Detect queries with performance degradation",
        icon="📊",
        required_slots=["db_type"],
        optional_slots=["connection_id", "baseline_period_days", "regression_threshold_percent"],
        source_allowed=["OPERATION"],
        playbook_name="QUERY_REGRESSION",  # May need to add to execution_plan_generator
    )
    
    # 10. Compare sp_Blitz vs Custom
    dba_use_case_metadata_registry.register(
        use_case_id="compare_sp_blitz_vs_custom",
        name="sp_Blitz vs Custom",
        description="Compare sp_Blitz findings with custom analysis",
        icon="⚖️",
        required_slots=["db_type"],
        optional_slots=["connection_id"],
        source_allowed=["OPERATION"],
        playbook_name="SP_BLITZ_COMPARISON",  # May need to add to execution_plan_generator
    )
    
    # 11. Incident Triage
    dba_use_case_metadata_registry.register(
        use_case_id="incident_triage",
        name="Incident Triage",
        description="Triage and analyze database incidents",
        icon="🚨",
        required_slots=["db_type"],
        optional_slots=["connection_id"],
        source_allowed=["OPERATION"],
        playbook_name="INCIDENT_TRIAGE",  # May need to add to execution_plan_generator
    )


# Auto-register on module import
register_all_use_case_metadata()

