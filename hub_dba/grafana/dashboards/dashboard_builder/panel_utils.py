"""
Grafana Panel Builder Utilities
Helper functions to create different panel types
"""

def create_target(expr, legend_format="", ref_id="A", format_type="time_series", instant=False):
    """Create a Prometheus query target"""
    target = {
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "editorMode": "code",
        "expr": expr,
        "refId": ref_id
    }
    
    if legend_format:
        target["legendFormat"] = legend_format
    
    if format_type == "table":
        target["format"] = "table"
    
    if instant:
        target["instant"] = True
    else:
        target["range"] = True
    
    return target


def create_stat_panel(panel_id, title, expr, x, y, w, h, 
                      thresholds, description="", unit="short", 
                      decimals=None, mappings=None, legend_format=""):
    """Create a stat panel with background color"""
    panel = {
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "description": description,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": thresholds,
                "unit": unit
            }
        },
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "textMode": "value_and_name",
            "wideLayout": True
        },
        "targets": [create_target(expr, legend_format)],
        "title": title,
        "type": "stat"
    }
    
    if decimals is not None:
        panel["fieldConfig"]["defaults"]["decimals"] = decimals
    
    if mappings:
        panel["fieldConfig"]["defaults"]["mappings"] = mappings
        panel["options"]["textMode"] = "value"
        panel["options"]["graphMode"] = "none"
    
    return panel


def create_gauge_panel(panel_id, title, expr, x, y, w, h,
                       thresholds, min_val=0, max_val=100,
                       unit="percent", description="", legend_format=""):
    """Create a gauge panel"""
    return {
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "description": description,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "max": max_val,
                "min": min_val,
                "thresholds": thresholds,
                "unit": unit
            }
        },
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {
            "minVizHeight": 75,
            "minVizWidth": 75,
            "orientation": "auto",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
            "sizing": "auto"
        },
        "targets": [create_target(expr, legend_format)],
        "title": title,
        "type": "gauge"
    }


def create_timeseries_panel(panel_id, title, targets, x, y, w, h,
                            description="", unit="short", fill_opacity=10,
                            stacking="none", show_legend=True):
    """Create a timeseries panel"""
    return {
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "description": description,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {
                    "axisBorderShow": False,
                    "axisCenteredZero": False,
                    "axisColorMode": "text",
                    "axisLabel": "",
                    "axisPlacement": "auto",
                    "barAlignment": 0,
                    "drawStyle": "line",
                    "fillOpacity": fill_opacity,
                    "gradientMode": "none" if stacking == "none" else "opacity",
                    "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                    "insertNulls": False,
                    "lineInterpolation": "smooth",
                    "lineWidth": 2,
                    "pointSize": 5,
                    "scaleDistribution": {"type": "linear"},
                    "showPoints": "never",
                    "spanNulls": False,
                    "stacking": {"group": "A", "mode": stacking},
                    "thresholdsStyle": {"mode": "off"}
                },
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}]
                },
                "unit": unit
            }
        },
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {
            "legend": {
                "calcs": ["mean", "max", "last"],
                "displayMode": "table",
                "placement": "bottom",
                "showLegend": show_legend
            },
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": targets,
        "title": title,
        "type": "timeseries"
    }


def create_table_panel(panel_id, title, expr, x, y, w, h,
                       exclude_cols=None, rename_cols=None,
                       description="", mappings=None, thresholds=None):
    """Create a table panel"""
    exclude_cols = exclude_cols or {"Time": True, "__name__": True, "job": True, "role": True, "tier": True}
    rename_cols = rename_cols or {}
    
    panel = {
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "description": description,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "custom": {
                    "align": "center",
                    "cellOptions": {"type": "color-background"},
                    "filterable": True,
                    "inspect": False
                },
                "mappings": mappings or [],
                "thresholds": thresholds or {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None}]
                }
            }
        },
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {
            "cellHeight": "sm",
            "footer": {
                "countRows": False,
                "fields": "",
                "reducer": ["sum"],
                "show": False
            },
            "showHeader": True
        },
        "targets": [create_target(expr, format_type="table", instant=True)],
        "title": title,
        "transformations": [{
            "id": "organize",
            "options": {
                "excludeByName": exclude_cols,
                "renameByName": rename_cols
            }
        }],
        "type": "table"
    }
    
    return panel


def create_piechart_panel(panel_id, title, expr, x, y, w, h,
                          description="", unit="decgbytes"):
    """Create a pie chart panel"""
    return {
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "description": description,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {
                    "hideFrom": {"legend": False, "tooltip": False, "viz": False}
                },
                "mappings": [],
                "unit": unit
            }
        },
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {
            "displayLabels": ["percent"],
            "legend": {
                "displayMode": "table",
                "placement": "bottom",
                "showLegend": True,
                "values": ["value"]
            },
            "pieType": "donut",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "tooltip": {"mode": "single", "sort": "none"}
        },
        "targets": [create_target(expr, legend_format="{{state}}")],
        "title": title,
        "type": "piechart"
    }


def create_row(row_id, title, y_pos):
    """Create a row separator"""
    return {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
        "id": row_id,
        "panels": [],
        "title": title,
        "type": "row"
    }


def create_alert_list_panel(panel_id, title, y_pos):
    """Create an Alert List panel"""
    return {
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": y_pos},
        "id": panel_id,
        "options": {
            "dashboardAlerts": True,
            "groupBy": [],
            "maxItems": 10,
            "show": "current",
            "sortOrder": 1,
            "stateFilter": ["firing", "pending"],
            "viewMode": "list"
        },
        "pluginVersion": "10.0.0",
        "title": title,
        "type": "alertlist"
    }


# Common threshold configurations
THRESHOLDS = {
    "agent_status": {
        "mode": "absolute",
        "steps": [
            {"color": "red", "value": None},
            {"color": "green", "value": 1}
        ]
    },
    "deadlocks": {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 0.01},
            {"color": "red", "value": 0.1}
        ]
    },
    "blocking": {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 5},
            {"color": "red", "value": 10}
        ]
    },
    "long_queries": {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 3},
            {"color": "red", "value": 5}
        ]
    },
    "user_errors": {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 5},
            {"color": "red", "value": 10}
        ]
    },
    "log_space": {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 70},
            {"color": "red", "value": 85}
        ]
    },
    "ple": {
        "mode": "absolute",
        "steps": [
            {"color": "red", "value": None},
            {"color": "yellow", "value": 300},
            {"color": "green", "value": 600}
        ]
    },
    "health_score": {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 3},
            {"color": "red", "value": 7}
        ]
    },
    "buffer_hit_ratio": {
        "mode": "absolute",
        "steps": [
            {"color": "red", "value": None},
            {"color": "yellow", "value": 80},
            {"color": "green", "value": 90}
        ]
    },
    "os_memory": {
        "mode": "absolute",
        "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 80},
            {"color": "red", "value": 90}
        ]
    }
}

# Common mappings
MAPPINGS = {
    "agent_status": [{
        "options": {
            "0": {"color": "red", "index": 0, "text": "🔴 STOPPED"},
            "1": {"color": "green", "index": 1, "text": "🟢 Running"}
        },
        "type": "value"
    }],
    "database_state": [{
        "options": {
            "0": {"color": "green", "index": 0, "text": "🟢 Online"},
            "1": {"color": "yellow", "index": 1, "text": "🟡 Restoring"},
            "2": {"color": "yellow", "index": 2, "text": "🟡 Recovering"},
            "3": {"color": "orange", "index": 3, "text": "🟠 Recovery Pending"},
            "4": {"color": "red", "index": 4, "text": "🔴 Suspect"},
            "5": {"color": "red", "index": 5, "text": "🔴 Emergency"},
            "6": {"color": "dark-red", "index": 6, "text": "⚫ Offline"}
        },
        "type": "value"
    }],
    "backup_status": [{
        "options": {
            "-1": {"color": "red", "index": 2, "text": "🔴 Critical"},
            "0": {"color": "yellow", "index": 1, "text": "🟡 Warning"},
            "1": {"color": "green", "index": 0, "text": "🟢 Healthy"}
        },
        "type": "value"
    }]
}
