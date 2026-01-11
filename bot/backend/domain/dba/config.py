"""
DBA Domain Configuration - Centralized settings and thresholds
"""
from typing import Dict, Optional
from enum import Enum


class DBAConfig:
    """Centralized DBA domain configuration and thresholds"""
    
    # ============================================================
    # BLOCKING THRESHOLDS
    # ============================================================
    # Critical blocking threshold - blocking > this duration is considered critical
    BLOCKING_CRITICAL_THRESHOLD_MS = 5000
    
    # ============================================================
    # IO PRESSURE THRESHOLDS
    # ============================================================
    # High I/O reads per second threshold
    IO_PRESSURE_HIGH_READS_PER_SEC = 100000
    # Medium I/O reads per second threshold
    IO_PRESSURE_MEDIUM_READS_PER_SEC = 10000
    
    # ============================================================
    # CAPACITY FORECAST CONFIG
    # ============================================================
    # Default monthly growth rate (percent) - configurable per tenant
    DEFAULT_MONTHLY_GROWTH_RATE = 10.0
    # Default database capacity max (1TB)
    DEFAULT_DATABASE_MAX_BYTES = 1_099_511_627_776
    # Warning threshold (80% of max)
    CAPACITY_WARNING_THRESHOLD = 0.8
    # Critical threshold (95% of max)
    CAPACITY_CRITICAL_THRESHOLD = 0.95
    
    # ============================================================
    # QUERY PERFORMANCE THRESHOLDS
    # ============================================================
    # Slow query threshold (default 1 second)
    SLOW_QUERY_THRESHOLD_MS = 1000
    # Query regression detection threshold (percent increase)
    QUERY_REGRESSION_THRESHOLD_PERCENT = 20.0
    
    # ============================================================
    # INCIDENT TRIAGE CONFIG
    # ============================================================
    # Incident types priority (lower = higher priority)
    INCIDENT_PRIORITY = {
        "DISK_SPACE": 1,
        "DEADLOCK": 2,
        "MEMORY_PRESSURE": 3,
        "CPU_PRESSURE": 4,
        "BLOCKING": 5,
        "CONNECTION_POOL_EXHAUSTED": 6,
        "SLOW_QUERY": 7,
        "OTHER": 8,
    }
    
    # ============================================================
    # PRODUCTION SAFETY FLAGS
    # ============================================================
    # Require explicit permission for production modifications
    REQUIRE_PROD_PERMISSION = True
    # Enable audit logging for all DBA operations
    ENABLE_AUDIT_LOG = True
    
    # ============================================================
    # RESPONSE VALIDATION
    # ============================================================
    # Validate response schemas from MCP
    VALIDATE_MCP_RESPONSES = True
    # Fail fast on validation errors
    FAIL_ON_VALIDATION_ERROR = True
    
    @classmethod
    def get_io_pressure_level(cls, total_reads: int) -> str:
        """
        Determine IO pressure level based on reads.
        
        Args:
            total_reads: Total reads count
            
        Returns:
            'high', 'medium', or 'low'
        """
        if total_reads > cls.IO_PRESSURE_HIGH_READS_PER_SEC:
            return "high"
        elif total_reads > cls.IO_PRESSURE_MEDIUM_READS_PER_SEC:
            return "medium"
        else:
            return "low"
    
    @classmethod
    def get_capacity_status(cls, forecasted_size: int) -> str:
        """
        Determine capacity status.
        
        Args:
            forecasted_size: Forecasted database size in bytes
            
        Returns:
            'critical', 'warning', or 'ok'
        """
        critical_threshold = cls.DEFAULT_DATABASE_MAX_BYTES * cls.CAPACITY_CRITICAL_THRESHOLD
        warning_threshold = cls.DEFAULT_DATABASE_MAX_BYTES * cls.CAPACITY_WARNING_THRESHOLD
        
        if forecasted_size >= critical_threshold:
            return "critical"
        elif forecasted_size >= warning_threshold:
            return "warning"
        else:
            return "ok"
