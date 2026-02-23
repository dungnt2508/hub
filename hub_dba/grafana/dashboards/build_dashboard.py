#!/usr/bin/env python3
"""
SQL Server Dashboard Generator
Generates comprehensive Grafana dashboard covering all 26 metrics
Usage: python build_dashboard.py
"""

import json
import sys
from pathlib import Path

# Add dashboard_builder to path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard_builder import (
    create_critical_alerts_row,
    create_kpis_row,
    create_memory_row,
    create_os_memory_row,
    create_storage_io_row,
    create_locks_row,
    create_connections_row,
    create_database_health_row,
    create_diagnostics_row
)


def create_base_dashboard():
    """Create base dashboard structure"""
    return {
        "annotations": {
            "list": [{
                "builtIn": 1,
                "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                "enable": True,
                "hide": True,
                "iconColor": "rgba(0, 211, 255, 1)",
                "name": "Annotations & Alerts",
                "type": "dashboard"
            }]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [{
            "asDropdown": False,
            "icon": "external link",
            "includeVars": True,
            "keepTime": True,
            "tags": [],
            "targetBlank": False,
            "title": "← Back to Overview",
            "tooltip": "",
            "type": "link",
            "url": "/d/sql-server-overview-prod/sql-server-overview-production"
        }],
        "panels": [],
        "refresh": "30s",
        "schemaVersion": 39,
        "tags": ["sql-server", "production", "instance-detail", "comprehensive"],
        "templating": {
            "list": [
                {
                    "current": {"selected": False, "text": "Prometheus", "value": "prometheus"},
                    "hide": 0,
                    "includeAll": False,
                    "label": "Data Source",
                    "multi": False,
                    "name": "datasource",
                    "options": [],
                    "query": "prometheus",
                    "queryValue": "",
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": False,
                    "type": "datasource"
                },
                {
                    "current": {"selected": False, "text": "", "value": ""},
                    "datasource": {"type": "prometheus", "uid": "${datasource}"},
                    "definition": "label_values(mssql_uptime_seconds, hostname)",
                    "hide": 0,
                    "includeAll": False,
                    "label": "Instance",
                    "multi": False,
                    "name": "instance",
                    "options": [],
                    "query": {
                        "qryType": 1,
                        "query": "label_values(mssql_uptime_seconds, hostname)",
                        "refId": "PrometheusVariableQueryEditor-VariableQuery"
                    },
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": False,
                    "sort": 1,
                    "type": "query"
                },
                {
                    "current": {"selected": False, "text": "", "value": ""},
                    "datasource": {"type": "prometheus", "uid": "${datasource}"},
                    "definition": "label_values(mssql_uptime_seconds{hostname=\"$instance\"}, environment)",
                    "hide": 0,
                    "includeAll": False,
                    "label": "Environment",
                    "multi": False,
                    "name": "environment",
                    "options": [],
                    "query": {
                        "qryType": 1,
                        "query": "label_values(mssql_uptime_seconds{hostname=\"$instance\"}, environment)",
                        "refId": "PrometheusVariableQueryEditor-VariableQuery"
                    },
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": False,
                    "sort": 1,
                    "type": "query"
                }
            ]
        },
        "time": {"from": "now-3h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "SQL Server - Instance Detail (Production)",
        "uid": "sql-server-instance-detail",
        "version": 1,
        "weekStart": ""
    }


def main():
    """Main dashboard generation function"""
    print("🚀 Generating SQL Server Comprehensive Dashboard...")
    
    # Create base dashboard
    dashboard = create_base_dashboard()
    
    # Track panel IDs and Y position
    panel_id = 1
    y_pos = 0
    
    # Row 1: Critical Alerts
    print("  ✅ Row 1: Critical Health Alerts (8 panels)")
    panels, panel_id, y_pos = create_critical_alerts_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 2: KPIs
    print("  ✅ Row 2: KPIs (3 panels)")
    panels, panel_id, y_pos = create_kpis_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 3: Memory
    print("  ✅ Row 3: Memory & Buffer Pool (4 panels)")
    panels, panel_id, y_pos = create_memory_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 4: OS Memory
    print("  ✅ Row 4: OS Memory (4 panels)")
    panels, panel_id, y_pos = create_os_memory_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 5: Storage/IO
    print("  ✅ Row 5: Storage & I/O Performance (4 panels)")
    panels, panel_id, y_pos = create_storage_io_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 6: Locks
    print("  ✅ Row 6: Locks & Blocking (4 panels)")
    panels, panel_id, y_pos = create_locks_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 7: Connections
    print("  ✅ Row 7: Connections & Sessions (3 panels)")
    panels, panel_id, y_pos = create_connections_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 8: Database Health
    print("  ✅ Row 8: Database Health & Backup (3 panels)")
    panels, panel_id, y_pos = create_database_health_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Row 9: Diagnostics
    print("  ✅ Row 9: Advanced Diagnostics (4 panels)")
    panels, panel_id, y_pos = create_diagnostics_row(panel_id, y_pos)
    dashboard["panels"].extend(panels)
    
    # Summary
    total_panels = len(dashboard["panels"])
    total_rows = sum(1 for p in dashboard["panels"] if p.get("type") == "row")
    total_visualization_panels = total_panels - total_rows
    
    print(f"\n📊 Dashboard Statistics:")
    print(f"  - Total Rows: {total_rows}")
    print(f"  - Total Panels: {total_visualization_panels}")
    print(f"  - Total Items: {total_panels}")
    print(f"  - Final Y Position: {y_pos}")
    
    # Write to file
    output_file = Path(__file__).parent / "SQL_Server_Instance_Detail_Production.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Dashboard generated successfully!")
    print(f"   Output: {output_file}")
    print(f"\n📝 Next Steps:")
    print(f"   1. Review the generated JSON file")
    print(f"   2. Import to Grafana: Configuration > Dashboards > Import")
    print(f"   3. Select Prometheus datasource")
    print(f"   4. Test with your SQL Server instances")
    
    return dashboard


if __name__ == "__main__":
    try:
        dashboard = main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error generating dashboard: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
