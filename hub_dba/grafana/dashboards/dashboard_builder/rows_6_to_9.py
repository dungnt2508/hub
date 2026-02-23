"""
Rows 6-9: Locks, Connections, Database Health, Diagnostics
Remaining panels for complete dashboard
"""

from .panel_utils import (
    create_row, create_timeseries_panel, create_table_panel,
    create_stat_panel, create_target, MAPPINGS
)


def create_locks_row(panel_id_start, y_pos):
    """Row 6: Locks & Blocking - 4 panels"""
    panels = []
    current_id = panel_id_start
    
    panels.append(create_row(current_id, "🔒 LOCKS & BLOCKING", y_pos))
    current_id += 1
    y_pos += 1
    
    # Deadlocks/s
    panels.append(create_timeseries_panel(
        current_id, "🔒 Deadlocks/sec",
        [create_target(
            'rate(mssql_deadlocks_total{hostname="$instance",environment="$environment"}[5m])',
            "Deadlocks"
        )],
        0, y_pos, 6, 6,
        description="Deadlock rate over time",
        unit="ops"
    ))
    current_id += 1
    
    # Blocking Sessions
    panels.append(create_timeseries_panel(
        current_id, "🚫 Blocking Sessions",
        [create_target(
            'mssql_blocking_session_count{hostname="$instance",environment="$environment"}',
            "Blocked"
        )],
        6, y_pos, 6, 6,
        description="Current blocking session count",
        unit="short"
    ))
    current_id += 1
    
    # Lock Waits
    panels.append(create_timeseries_panel(
        current_id, "⏳ Lock Waits/sec",
        [create_target(
            'rate(mssql_lock_waits_total{hostname="$instance",environment="$environment"}[1m])',
            "Lock Waits"
        )],
        12, y_pos, 6, 6,
        description="Lock wait events per second",
        unit="ops"
    ))
    current_id += 1
    
    # Lock Timeouts
    panels.append(create_timeseries_panel(
        current_id, "⏰ Lock Timeouts/sec",
        [create_target(
            'rate(mssql_lock_timeouts_total{hostname="$instance",environment="$environment"}[1m])',
            "Timeouts"
        )],
        18, y_pos, 6, 6,
        description="Lock timeout events per second",
        unit="ops"
    ))
    
    return panels, current_id + 1, y_pos + 6


def create_connections_row(panel_id_start, y_pos):
    """Row 7: Connections & Sessions - 3 panels"""
    panels = []
    current_id = panel_id_start
    
    panels.append(create_row(current_id, "🔌 CONNECTIONS & SESSIONS", y_pos))
    current_id += 1
    y_pos += 1
    
    # Connections by DB
    panels.append(create_timeseries_panel(
        current_id, "🔌 Connections by Database",
        [create_target(
            'mssql_connections{hostname="$instance",environment="$environment"}',
            "{{db}}"
        )],
        0, y_pos, 12, 6,
        description="Active connections per database",
        unit="short",
        stacking="normal",
        fill_opacity=20
    ))
    current_id += 1
    
    # Total Connections
    panels.append(create_stat_panel(
        current_id, "📊 Total Connections",
        'sum(mssql_connections{hostname="$instance",environment="$environment"})',
        12, y_pos, 4, 6,
        {"mode": "absolute", "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 300},
            {"color": "red", "value": 500}
        ]},
        description="Total active connections across all databases"
    ))
    current_id += 1
    
    # Long Queries
    panels.append(create_timeseries_panel(
        current_id, "⏱️ Long Running Queries (>30s)",
        [create_target(
            'mssql_long_running_queries{hostname="$instance",environment="$environment"}',
            "Long Queries"
        )],
        16, y_pos, 8, 6,
        description="Number of queries running >30 seconds",
        unit="short"
    ))
    
    return panels, current_id + 1, y_pos + 6


def create_database_health_row(panel_id_start, y_pos):
    """Row 8: Database Health & Backup - 3 panels"""
    panels = []
    current_id = panel_id_start
    
    panels.append(create_row(current_id, "💿 DATABASE HEALTH & BACKUP", y_pos))
    current_id += 1
    y_pos += 1
    
    # Database State
    panels.append(create_table_panel(
        current_id, "💿 Database State",
        'mssql_database_state{hostname="$instance",environment="$environment"}',
        0, y_pos, 8, 7,
        exclude_cols={"Time": True, "__name__": True, "job": True, "hostname": True, "environment": True, "role": True, "tier": True},
        rename_cols={"db": "Database", "Value": "State"},
        description="Database online/offline status",
        mappings=MAPPINGS["database_state"]
    ))
    current_id += 1
    
    # Backup Status
    panels.append(create_table_panel(
        current_id, "💾 Backup Status",
        'mssql_backup_status{hostname="$instance",environment="$environment"}',
        8, y_pos, 8, 7,
        exclude_cols={"Time": True, "__name__": True, "job": True, "hostname": True, "environment": True, "role": True, "tier": True},
        rename_cols={"db": "Database", "backup_type": "Type", "Value": "Status"},
        description="Backup compliance status",
        mappings=MAPPINGS["backup_status"]
    ))
    current_id += 1
    
    # Database Size
    panels.append(create_timeseries_panel(
        current_id, "📊 Database Size (GB)",
        [create_target(
            'sum by(db) (mssql_database_size_gb{hostname="$instance",environment="$environment"})',
            "{{db}}"
        )],
        16, y_pos, 8, 7,
        description="Database size growth over time",
        unit="decgbytes"
    ))
    
    return panels, current_id + 1, y_pos + 7


def create_diagnostics_row(panel_id_start, y_pos):
    """Row 9: Advanced Diagnostics - 4 panels"""
    panels = []
    current_id = panel_id_start
    
    panels.append(create_row(current_id, "🔍 ADVANCED DIAGNOSTICS", y_pos))
    current_id += 1
    y_pos += 1
    
    # Wait Stats
    panels.append(create_timeseries_panel(
        current_id, "🚥 Wait Statistics (ms/sec)",
        [create_target(
            'rate(mssql_wait_stats_ms_total{hostname="$instance",environment="$environment",stat_type="wait_time_ms"}[5m])',
            "{{wait_type}}"
        )],
        0, y_pos, 12, 9,
        description="Top wait types - identify performance bottlenecks",
        unit="ms",
        stacking="normal",
        fill_opacity=30
    ))
    current_id += 1
    
    # Blitz Findings
    panels.append(create_table_panel(
        current_id, "🛡️ Blitz Health Findings",
        'mssql_blitz_findings{hostname="$instance",environment="$environment"}',
        12, y_pos, 6, 9,
        exclude_cols={"Time": True, "__name__": True, "job": True, "hostname": True, "environment": True, "role": True, "tier": True},
        rename_cols={"priority": "Priority", "findings_group": "Category", "Value": "Count"},
        description="Health check findings from Blitz scripts"
    ))
    current_id += 1
    
    # Top CPU Queries (Blitz Cache)
    panels.append(create_table_panel(
        current_id, "🔥 Top CPU Queries",
        'mssql_blitz_cache_cpu_top10{hostname="$instance",environment="$environment"}',
        18, y_pos, 6, 9,
        exclude_cols={"Time": True, "__name__": True, "job": True, "hostname": True, "environment": True},
        rename_cols={"query_hash": "Query Hash", "cpu_ms": "CPU (ms)", "Value": "Executions"},
        description="Top 10 CPU consuming queries (from Blitz Cache)"
    ))
    current_id += 1
    
    # Blitz Snapshot Age
    panels.append(create_stat_panel(
        current_id, "⏰ Blitz Snapshot Age",
        'mssql_blitz_snapshot_age_hours{hostname="$instance",environment="$environment"}',
        0, y_pos + 9, 24, 3,
        {"mode": "absolute", "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 3},
            {"color": "red", "value": 6}
        ]},
        description="Hours since last Blitz scripts run - watchdog for Agent Jobs",
        unit="h"
    ))
    
    return panels, current_id + 1, y_pos + 12
