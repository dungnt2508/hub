"""
Row 2: Key Performance Indicators (KPIs)
3 panels for high-level activity metrics
"""

from .panel_utils import create_row, create_stat_panel, create_timeseries_panel, create_target


def create_kpis_row(panel_id_start, y_pos):
    """Create KPIs row with 3 panels"""
    panels = []
    current_id = panel_id_start
    
    # Row header
    panels.append(create_row(current_id, "📊 KEY PERFORMANCE INDICATORS", y_pos))
    current_id += 1
    y_pos += 1
    
    # Panel 1: Uptime
    panels.append(create_stat_panel(
        current_id, "⏰ Uptime",
        'mssql_uptime_seconds{hostname="$instance",environment="$environment"}',
        0, y_pos, 6, 5,
        {"mode": "absolute", "steps": [{"color": "blue", "value": None}]},
        description="SQL Server uptime",
        unit="s"
    ))
    current_id += 1
    
    # Panel 2: Batch Requests/s
    panels.append(create_timeseries_panel(
        current_id, "📊 Batch Requests/sec",
        [create_target(
            'rate(mssql_batch_requests_total{hostname="$instance",environment="$environment"}[1m])',
            "Batch Req/s"
        )],
        6, y_pos, 9, 5,
        description="Batch requests per second - overall activity throughput",
        unit="ops"
    ))
    current_id += 1
    
    # Panel 3: Logins/s
    panels.append(create_timeseries_panel(
        current_id, "🔐 Logins/sec",
        [create_target(
            'rate(mssql_logins_total{hostname="$instance",environment="$environment"}[1m])',
            "Logins/s"
        )],
        15, y_pos, 9, 5,
        description="Login rate - connection pooling indicator",
        unit="ops"
    ))
    
    return panels, current_id + 1, y_pos + 5
