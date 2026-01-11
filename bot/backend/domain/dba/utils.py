"""
DBA Domain Utilities
Provides utility functions for DBA use cases
"""

from typing import Optional, Dict, Any, List
from .ports.mcp_client import DatabaseType


class DBAnalysisUtils:
    """Utility class for database analysis"""
    
    @staticmethod
    def calculate_growth_rate(
        current_value: float,
        previous_value: Optional[float] = None,
        days_passed: int = 30
    ) -> float:
        """
        Calculate growth rate as percentage.
        
        Args:
            current_value: Current metric value
            previous_value: Previous metric value (optional)
            days_passed: Days between measurements (default: 30)
            
        Returns:
            Growth rate as percentage
        """
        if previous_value is None or previous_value == 0:
            return 0.0
        
        growth = current_value - previous_value
        rate = (growth / previous_value) * 100
        
        # Annualize the rate
        annualized_rate = rate * (365 / days_passed)
        return annualized_rate
    
    @staticmethod
    def estimate_time_to_exhaustion(
        current_value: float,
        max_value: float,
        growth_rate_percent: float,
        days_per_period: int = 30
    ) -> Optional[float]:
        """
        Estimate days until resource exhaustion.
        
        Args:
            current_value: Current resource usage
            max_value: Maximum resource value
            growth_rate_percent: Growth rate as percentage per period
            days_per_period: Days per growth period (default: 30)
            
        Returns:
            Estimated days to exhaustion or None if no growth
        """
        if growth_rate_percent == 0:
            return None
        
        if current_value >= max_value:
            return 0.0
        
        # Calculate using exponential growth formula
        # V = V0 * (1 + r)^t
        # t = ln(V/V0) / ln(1 + r)
        import math
        
        growth_factor = 1 + (growth_rate_percent / 100)
        if growth_factor <= 1:
            return None
        
        days = math.log(max_value / current_value) / math.log(growth_factor) * days_per_period
        return max(days, 0)
    
    @staticmethod
    def normalize_time_to_ms(value: Any, unit: Optional[str] = None) -> Optional[float]:
        """
        Normalize time value to milliseconds.
        
        Args:
            value: Time value to normalize
            unit: Original unit (None for auto-detect, 'ms', 's', 'us', 'ns')
            
        Returns:
            Time in milliseconds or None
        """
        if value is None:
            return None
        
        if not isinstance(value, (int, float)):
            return None
        
        if unit is None:
            # Auto-detect based on magnitude
            if value > 1e12:
                return value / 1e6  # nanoseconds to ms
            elif value > 1e6:
                return value / 1000  # microseconds to ms
            elif value > 1000:
                return value  # assume already in ms
            else:
                return value * 1000  # seconds to ms
        elif unit == "ns":
            return value / 1e6
        elif unit == "us":
            return value / 1000
        elif unit == "ms":
            return value
        elif unit == "s":
            return value * 1000
        else:
            return value
    
    @staticmethod
    def normalize_size_to_bytes(value: Any, unit: Optional[str] = None) -> Optional[int]:
        """
        Normalize size value to bytes.
        
        Args:
            value: Size value to normalize
            unit: Original unit (None for auto-detect, 'bytes', 'kb', 'mb', 'gb', 'tb')
            
        Returns:
            Size in bytes or None
        """
        if value is None:
            return None
        
        if not isinstance(value, (int, float)):
            return None
        
        value = int(value)
        
        if unit is None:
            # Auto-detect based on magnitude
            if value > 1e12:
                return value  # assume already in bytes
            elif value > 1e9:
                return value * 1024  # assume GB
            elif value > 1e6:
                return value * 1024 * 1024  # assume MB
            elif value > 1e3:
                return value * 1024 * 1024 * 1024  # assume GB
            else:
                return value
        elif unit.lower() == "bytes" or unit.lower() == "b":
            return value
        elif unit.lower() == "kb":
            return value * 1024
        elif unit.lower() == "mb":
            return value * 1024 * 1024
        elif unit.lower() == "gb":
            return value * 1024 * 1024 * 1024
        elif unit.lower() == "tb":
            return value * 1024 * 1024 * 1024 * 1024
        else:
            return value
    
    @staticmethod
    def categorize_severity(
        metric_value: float,
        thresholds: Dict[str, float]
    ) -> str:
        """
        Categorize severity based on metric value and thresholds.
        
        Args:
            metric_value: Metric value to categorize
            thresholds: Dictionary with threshold keys ('critical', 'warning', 'ok')
                       Example: {'critical': 100, 'warning': 50}
                       
        Returns:
            Severity level: 'critical', 'warning', or 'ok'
        """
        critical_threshold = thresholds.get("critical", 100)
        warning_threshold = thresholds.get("warning", 50)
        
        if metric_value >= critical_threshold:
            return "critical"
        elif metric_value >= warning_threshold:
            return "warning"
        else:
            return "ok"
    
    @staticmethod
    def get_recommendation_for_severity(
        severity: str,
        metric_name: str,
        metric_value: Optional[float] = None
    ) -> str:
        """
        Get recommendation based on severity level.
        
        Args:
            severity: Severity level ('critical', 'warning', 'ok')
            metric_name: Name of the metric (for context)
            metric_value: Current metric value (optional)
            
        Returns:
            Recommendation string
        """
        if severity == "critical":
            return f"CRITICAL: {metric_name} needs immediate attention (value: {metric_value})"
        elif severity == "warning":
            return f"WARNING: {metric_name} should be monitored closely (value: {metric_value})"
        else:
            return f"OK: {metric_name} is within acceptable range (value: {metric_value})"
    
    @staticmethod
    def format_bytes(size_bytes: int) -> str:
        """
        Format bytes into human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    def format_duration_ms(duration_ms: float) -> str:
        """
        Format milliseconds into human-readable format.
        
        Args:
            duration_ms: Duration in milliseconds
            
        Returns:
            Formatted duration string
        """
        if duration_ms < 1:
            return f"{duration_ms * 1000:.2f} µs"
        elif duration_ms < 1000:
            return f"{duration_ms:.2f} ms"
        elif duration_ms < 60000:
            return f"{duration_ms / 1000:.2f} s"
        elif duration_ms < 3600000:
            return f"{duration_ms / 60000:.2f} min"
        else:
            return f"{duration_ms / 3600000:.2f} h"
    
    @staticmethod
    def get_database_specific_advice(db_type: DatabaseType, issue_type: str) -> List[str]:
        """
        Get database-specific advice for common issues.
        
        Args:
            db_type: Database type
            issue_type: Type of issue (e.g., 'slow_query', 'blocking', 'index_fragmentation')
            
        Returns:
            List of recommendations
        """
        advice_map = {
            DatabaseType.POSTGRESQL: {
                "slow_query": [
                    "Use EXPLAIN ANALYZE to examine query plan",
                    "Check if indexes exist on WHERE/JOIN columns",
                    "Consider using ANALYZE command to update statistics",
                    "Use pg_stat_statements to identify top queries",
                ],
                "blocking": [
                    "Use pg_stat_activity to identify blocking sessions",
                    "Check transaction isolation levels",
                    "Consider using advisory locks for application coordination",
                    "May need to kill blocking process if necessary",
                ],
                "index_fragmentation": [
                    "Use REINDEX command to rebuild indexes",
                    "Consider using CLUSTER command for heap reorganization",
                    "Monitor using pg_stat_user_indexes",
                ],
            },
            DatabaseType.MYSQL: {
                "slow_query": [
                    "Enable slow query log to capture slow queries",
                    "Use EXPLAIN to analyze query execution",
                    "Consider adding indexes on filtered/joined columns",
                    "Check if query cache is beneficial",
                ],
                "blocking": [
                    "Check SHOW INNODB STATUS for blocking information",
                    "Adjust innodb_lock_wait_timeout if needed",
                    "Review transaction isolation level (READ COMMITTED is usually better)",
                    "Use pt-deadlock-logger to track deadlocks",
                ],
                "index_fragmentation": [
                    "Use OPTIMIZE TABLE to rebuild table and indexes",
                    "Monitor using SHOW TABLE STATUS",
                    "Consider setting innodb_file_per_table for better management",
                ],
            },
            DatabaseType.SQLSERVER: {
                "slow_query": [
                    "Use SET STATISTICS IO/TIME to check I/O operations",
                    "Examine actual execution plans",
                    "Check if statistics are up-to-date (sp_updatestats)",
                    "Use Query Store to track query performance over time",
                ],
                "blocking": [
                    "Use sp_who2 or sp_blocker_pids88 to identify blockers",
                    "Check sys.dm_exec_requests for blocked sessions",
                    "Review transaction isolation levels",
                    "Use sp_kill to terminate blocking processes if needed",
                ],
                "index_fragmentation": [
                    "Use DBCC SHOWCONTIG to check fragmentation",
                    "Use ALTER INDEX REORGANIZE for < 30% fragmentation",
                    "Use ALTER INDEX REBUILD for > 30% fragmentation",
                    "Schedule index maintenance during off-peak hours",
                ],
            },
        }
        
        db_advice = advice_map.get(db_type, {})
        return db_advice.get(issue_type, ["No specific advice available for this database and issue type"])
