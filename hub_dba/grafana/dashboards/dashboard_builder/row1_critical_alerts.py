"""
Row 1: Critical Health Alerts
8 panels for immediate problem identification
"""

from .panel_utils import (
    create_row, create_stat_panel, create_gauge_panel, create_table_panel,
    create_target, THRESHOLDS, MAPPINGS
)


def create_critical_alerts_row(panel_id_start, y_pos):
    """Create Critical Health Alerts row with 8 panels"""
    panels = []
    current_id = panel_id_start
    
    # Row header
    panels.append(create_row(current_id, "🚨 CRITICAL HEALTH ALERTS", y_pos))
    current_id += 1
    y_pos += 1
    
    # Panel 1: Agent Status
    panels.append(create_stat_panel(
        current_id, "🤖 Agent",
        'mssql_agent_status{hostname="$instance",environment="$environment"}',
        0, y_pos, 6, 4,
        THRESHOLDS["agent_status"],
        description="SQL Server Agent status - CRITICAL if stopped",
        mappings=MAPPINGS["agent_status"]
    ))
    current_id += 1
    
    # Panel 2: Deadlocks
    panels.append(create_stat_panel(
        current_id, "🔒 Deadlocks",
        'rate(mssql_deadlocks_total{hostname="$instance",environment="$environment"}[5m])',
        6, y_pos, 6, 4,
        THRESHOLDS["deadlocks"],
        description="Deadlocks per second - CRITICAL if > 0.1/s",
        unit="ops",
        decimals=3,
        legend_format="Deadlocks/s"
    ))
    current_id += 1
    
    # Panel 3: Blocking
    panels.append(create_stat_panel(
        current_id, "🚫 Blocking",
        'mssql_blocking_session_count{hostname="$instance",environment="$environment"}',
        12, y_pos, 6, 4,
        THRESHOLDS["blocking"],
        description="Blocked sessions - CRITICAL if > 10",
        legend_format="Blocking"
    ))
    current_id += 1
    
    # Panel 4: Long Queries
    panels.append(create_stat_panel(
        current_id, "⏱️ Long Queries",
        'mssql_long_running_queries{hostname="$instance",environment="$environment"}',
        18, y_pos, 6, 4,
        THRESHOLDS["long_queries"],
        description="Long running queries (>30s) - CRITICAL if > 5",
        legend_format="Long Queries"
    ))
    current_id += 1
    y_pos += 4

    # Panel 5: User Errors
    panels.append(create_stat_panel(
        current_id, "⚠️ User Errors",
        'rate(mssql_user_errors_total{hostname="$instance",environment="$environment"}[5m])',
        0, y_pos, 6, 4,
        THRESHOLDS["user_errors"],
        description="User errors per second - WARNING if > 10/s",
        unit="ops",
        decimals=2,
        legend_format="Errors/s"
    ))
    current_id += 1
    
    # Panel 6: Log Space
    panels.append(create_gauge_panel(
        current_id, "📊 Log Space",
        'max(mssql_log_space_used_percent{hostname="$instance",environment="$environment",stat="log_space_used_percent"})',
        6, y_pos, 6, 4,
        THRESHOLDS["log_space"],
        min_val=0,
        max_val=100,
        unit="percent",
        description="Transaction log space - CRITICAL if > 85%",
        legend_format="Max Log %"
    ))
    current_id += 1
    
    # Panel 7: PLE
    panels.append(create_gauge_panel(
        current_id, "🧠 PLE",
        'mssql_page_life_expectancy_seconds{hostname="$instance",environment="$environment"}',
        12, y_pos, 6, 4,
        THRESHOLDS["ple"],
        min_val=0,
        max_val=1200,
        unit="s",
        description="Page Life Expectancy - CRITICAL if < 300s",
        legend_format="PLE"
    ))
    current_id += 1
    
    # Panel 8: Health Score
    zero_val = '(mssql_uptime_seconds{hostname="$instance", environment="$environment"} * 0)'
    health_score_expr = f'''(
  ((sum by(hostname, environment) (mssql_connections{{hostname="$instance", environment="$environment"}}) >bool 500) * 2 or on(hostname, environment) {zero_val})
  + on(hostname, environment) ((rate(mssql_deadlocks_total{{hostname="$instance", environment="$environment"}}[5m]) >bool 0.1) * 3 or on(hostname, environment) {zero_val})
  + on(hostname, environment) ((mssql_blocking_session_count{{hostname="$instance", environment="$environment"}} >bool 10) * 2 or on(hostname, environment) {zero_val})
  + on(hostname, environment) ((mssql_agent_status{{hostname="$instance", environment="$environment"}} ==bool 0) * 5 or on(hostname, environment) {zero_val})
  + on(hostname, environment) ((mssql_long_running_queries{{hostname="$instance", environment="$environment"}} >bool 5) * 2 or on(hostname, environment) {zero_val})
  + on(hostname, environment) ((mssql_page_life_expectancy_seconds{{hostname="$instance", environment="$environment"}} <bool 300) * 2 or on(hostname, environment) {zero_val})
  + on(hostname, environment) ((count by(hostname, environment) (mssql_backup_status{{hostname="$instance", environment="$environment", backup_type="Full"}} != 1) >bool 0) * 1 or on(hostname, environment) {zero_val})
  + on(hostname, environment) ((count by(hostname, environment) (mssql_database_state{{hostname="$instance", environment="$environment"}} != 0) >bool 0) * 3 or on(hostname, environment) {zero_val})
)'''
    
    panels.append(create_stat_panel(
        current_id, "🏥 Health Score",
        health_score_expr,
        18, y_pos, 6, 4,
        THRESHOLDS["health_score"],
        description="Overall health score - higher is worse",
        legend_format="Score"
    ))
    current_id += 1
    y_pos += 4

    # NEW: Panel 9 - Health Score Details (Table - Row by Row)
    # displaying: Hostname | Metric Name | Value
    details_panel = create_table_panel(
        current_id, "📋 Drill Down: Health Score Details",
        'label_replace(mssql_connections{hostname="$instance",environment="$environment"}, "metric", "Connections", "", "")',
        0, y_pos, 24, 8,
        description="Detailed metrics contributing to Health Score per instance"
    )
    
    # helper to create a target with a specific metric label
    def create_detail_target(expr, name, ref_id):
        return create_target(
            f'label_replace({expr}, "metric", "{name}", "", "")',
            "", ref_id=ref_id, format_type="table", instant=True
        )

    details_panel["targets"] = [
        create_detail_target('mssql_connections{hostname="$instance",environment="$environment"}', "Connections", "A"),
        create_detail_target('rate(mssql_deadlocks_total{hostname="$instance",environment="$environment"}[5m])', "Deadlocks", "B"),
        create_detail_target('mssql_blocking_session_count{hostname="$instance",environment="$environment"}', "Blocking", "C"),
        create_detail_target('mssql_agent_status{hostname="$instance",environment="$environment"}', "Agent Status", "D"),
        create_detail_target('mssql_long_running_queries{hostname="$instance",environment="$environment"}', "Long Queries", "E"),
        create_detail_target('mssql_page_life_expectancy_seconds{hostname="$instance",environment="$environment"}', "PLE", "F"),
        create_detail_target('count by(hostname, environment) (mssql_backup_status{hostname="$instance",environment="$environment", backup_type="Full"} != 1)', "Backup Failures", "G"),
        create_detail_target('count by(hostname, environment) (mssql_database_state{hostname="$instance",environment="$environment"} != 0)', "DB State Issues", "H"),
    ]
    
    # Transformation: Labels to Fields (to see 'metric') -> Organize (to rename/hide)
    # Note: When multiple targets return tables with same columns, Grafana Table panel often vertically stacks them (concatenates) by default or via "Merge" if they share time. 
    # But "concatenation" usually happens automatically for compatible frames in Table view.
    details_panel["transformations"] = [
        {"id": "labelsToFields", "options": {}},
        {"id": "organize", "options": {
            "excludeByName": {"Time": True, "__name__": True, "job": True, "environment": True, "role": True, "tier": True},
            "renameByName": {"metric": "Metric", "Value": "Value", "hostname": "Instance"},
            "indexByName": {"Instance": 0, "Metric": 1, "Value": 2}
        }}
    ]
    panels.append(details_panel)
    current_id += 1
    
    return panels, current_id + 1, y_pos + 8
