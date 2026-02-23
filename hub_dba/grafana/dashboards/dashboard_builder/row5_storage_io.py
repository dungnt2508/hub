"""
Row 5: Storage & I/O Performance
4 panels for disk latency and log health
"""

from .panel_utils import create_row, create_timeseries_panel, create_target


def create_storage_io_row(panel_id_start, y_pos):
    """Create Storage & I/O row with 4 panels"""
    panels = []
    current_id = panel_id_start
    
    # Row header
    panels.append(create_row(current_id, "💾 STORAGE & I/O PERFORMANCE", y_pos))
    current_id += 1
    y_pos += 1
    
    # Panel 1: Read Latency
    panels.append(create_timeseries_panel(
        current_id, "📖 Read Latency (ms)",
        [create_target(
            'rate(mssql_io_stall_ms_total{hostname="$instance",environment="$environment",io_type="io_stall_read_ms"}[1m]) / ignoring(io_type) rate(mssql_io_stall_ms_total{hostname="$instance",environment="$environment",io_type="num_of_reads"}[1m])',
            "{{db}}"
        )],
        0, y_pos, 6, 7,
        description="Average read latency per database (< 20ms = good, > 50ms = investigate)",
        unit="ms"
    ))
    current_id += 1
    
    # Panel 2: Write Latency
    panels.append(create_timeseries_panel(
        current_id, "✍️ Write Latency (ms)",
        [create_target(
            'rate(mssql_io_stall_ms_total{hostname="$instance",environment="$environment",io_type="io_stall_write_ms"}[1m]) / ignoring(io_type) rate(mssql_io_stall_ms_total{hostname="$instance",environment="$environment",io_type="num_of_writes"}[1m])',
            "{{db}}"
        )],
        6, y_pos, 6, 7,
        description="Average write latency per database (< 10ms = good, > 30ms = investigate)",
        unit="ms"
    ))
    current_id += 1
    
    # Panel 3: Log Space Used %
    panels.append(create_timeseries_panel(
        current_id, "📊 Transaction Log Space %",
        [create_target(
            'mssql_log_space_used_percent{hostname="$instance",environment="$environment",stat="log_space_used_percent"}',
            "{{db}}"
        )],
        12, y_pos, 6, 7,
        description="Transaction log space used per database",
        unit="percent"
    ))
    current_id += 1
    
    # Panel 4: Log Size
    panels.append(create_timeseries_panel(
        current_id, "📂 Transaction Log Size (MB)",
        [create_target(
            'mssql_log_space_used_percent{hostname="$instance",environment="$environment",stat="log_size_mb"}',
            "{{db}}"
        )],
        18, y_pos, 6, 7,
        description="Transaction log file size per database",
        unit="decmbytes"
    ))
    
    return panels, current_id + 1, y_pos + 7
