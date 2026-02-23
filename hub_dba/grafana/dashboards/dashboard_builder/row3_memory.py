"""
Row 3: Memory & Buffer Pool
4 panels for memory performance
"""

from .panel_utils import (
    create_row, create_timeseries_panel, create_gauge_panel,
    create_target, THRESHOLDS
)


def create_memory_row(panel_id_start, y_pos):
    """Create Memory & Buffer Pool row with 4 panels"""
    panels = []
    current_id = panel_id_start
    
    # Row header
    panels.append(create_row(current_id, "🧠 MEMORY & BUFFER POOL", y_pos))
    current_id += 1
    y_pos += 1
    
    # Panel 1: SQL Server Memory
    panels.append(create_timeseries_panel(
        current_id, "💾 SQL Server Memory (GB)",
        [
            create_target(
                'mssql_memory_usage_gb{hostname="$instance",environment="$environment",memory_type="resident_gb"}',
                "Resident (Working Set)"
            ),
            create_target(
                'mssql_memory_usage_gb{hostname="$instance",environment="$environment",memory_type="virtual_gb"}',
                "Virtual (Committed)", ref_id="B"
            )
        ],
        0, y_pos, 10, 6,
        description="SQL Server memory usage - Resident vs Virtual",
        unit="decgbytes",
        fill_opacity=20
    ))
    current_id += 1
    
    # Panel 2: Buffer Hit Ratio
    panels.append(create_gauge_panel(
        current_id, "💿 Buffer Cache Hit Ratio",
        'mssql_buffer_cache_hit_ratio{hostname="$instance",environment="$environment"}',
        10, y_pos, 4, 6,
        THRESHOLDS["buffer_hit_ratio"],
        min_val=0,
        max_val=100,
        unit="percent",
        description="Buffer cache hit ratio - should be > 90%"
    ))
    current_id += 1
    
    # Panel 3: Page Life Expectancy
    panels.append(create_timeseries_panel(
        current_id, "🧠 Page Life Expectancy",
        [create_target(
            'mssql_page_life_expectancy_seconds{hostname="$instance",environment="$environment"}',
            "PLE (seconds)"
        )],
        14, y_pos, 5, 6,
        description="Page Life Expectancy - MIN across all NUMA nodes. Threshold: <300s = memory pressure",
        unit="s"
    ))
    current_id += 1
    
    # Panel 4: Lazy Writes
    panels.append(create_timeseries_panel(
        current_id, "🚨 Lazy Writes/sec",
        [create_target(
            'rate(mssql_lazy_writes_total{hostname="$instance",environment="$environment"}[1m])',
            "Lazy Writes/s"
        )],
        19, y_pos, 5, 6,
        description="Lazy writes - indicator of memory pressure (buffer pool thrashing)",
        unit="ops"
    ))
    
    return panels, current_id + 1, y_pos + 6
