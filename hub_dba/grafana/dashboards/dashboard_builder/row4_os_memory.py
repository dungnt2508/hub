"""
Row 4: OS Memory
4 panels for operating system memory
"""

from .panel_utils import (
    create_row, create_gauge_panel, create_piechart_panel,
    create_stat_panel, create_timeseries_panel, create_target,
    THRESHOLDS
)


def create_os_memory_row(panel_id_start, y_pos):
    """Create OS Memory row with 4 panels"""
    panels = []
    current_id = panel_id_start
    
    # Row header
    panels.append(create_row(current_id, "💽 OS MEMORY", y_pos))
    current_id += 1
    y_pos += 1
    
    # Panel 1: OS Memory Usage %
    panels.append(create_gauge_panel(
        current_id, "💽 OS Memory Usage %",
        '(mssql_os_memory{hostname="$instance",environment="$environment",state="used"} / ignoring(state) mssql_os_memory_total_gb{hostname="$instance",environment="$environment"}) * 100',
        0, y_pos, 6, 5,
        THRESHOLDS["os_memory"],
        min_val=0,
        max_val=100,
        unit="percent",
        description="OS memory usage percentage"
    ))
    current_id += 1
    
    # Panel 2: OS Memory Breakdown
    panels.append(create_piechart_panel(
        current_id, "📊 OS Memory Breakdown",
        'mssql_os_memory{hostname="$instance",environment="$environment"}',
        6, y_pos, 6, 5,
        description="OS memory breakdown (used/available)",
        unit="decgbytes"
    ))
    current_id += 1
    
    # Panel 3: Total OS Memory
    panels.append(create_stat_panel(
        current_id, "💾 Total OS Memory",
        'mssql_os_memory_total_gb{hostname="$instance",environment="$environment"}',
        12, y_pos, 4, 5,
        {"mode": "absolute", "steps": [{"color": "blue", "value": None}]},
        description="Total physical memory in the server",
        unit="decgbytes"
    ))
    current_id += 1
    
    # Panel 4: SQL vs OS Memory Trend
    panels.append(create_timeseries_panel(
        current_id, "📈 SQL vs OS Memory Trend",
        [
            create_target(
                'mssql_memory_usage_gb{hostname="$instance",environment="$environment",memory_type="resident_gb"}',
                "SQL Resident"
            ),
            create_target(
                'mssql_os_memory{hostname="$instance",environment="$environment",state="used"}',
                "OS Used", ref_id="B"
            ),
            create_target(
                'mssql_os_memory_total_gb{hostname="$instance",environment="$environment"}',
                "OS Total", ref_id="C"
            )
        ],
        16, y_pos, 8, 5,
        description="SQL Server memory vs OS memory over time",
        unit="decgbytes"
    ))
    
    return panels, current_id + 1, y_pos + 5
