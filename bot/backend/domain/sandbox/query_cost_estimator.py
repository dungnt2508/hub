"""
Query Cost Estimator - Estimates query execution cost and performance impact
"""
import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

@dataclass
class TableStats:
    """Table statistics for cost estimation"""
    name: str
    row_count: int
    avg_row_size_bytes: int = 100


class QueryCostEstimator:
    """Estimates query cost and performance impact"""

    # Mock table statistics for demonstration
    MOCK_TABLE_STATS = {
        'users': TableStats('users', 100000),
        'transactions': TableStats('transactions', 5000000),
        'logs': TableStats('logs', 50000000),
        'sessions': TableStats('sessions', 500000),
        'products': TableStats('products', 10000),
        'orders': TableStats('orders', 1000000),
        'employees': TableStats('employees', 5000),
        'customers': TableStats('customers', 100000),
        'sys.dm_exec_requests': TableStats('sys.dm_exec_requests', 100),
        'sys.tables': TableStats('sys.tables', 5000),
        'information_schema.tables': TableStats('information_schema.tables', 5000),
    }

    # Cost factors
    COST_FACTORS = {
        'full_table_scan': 1.0,  # Baseline
        'index_seek': 0.1,
        'index_scan': 0.3,
        'join': 0.5,
        'sort': 0.2,
        'group_by': 0.3,
        'distinct': 0.2,
        'subquery': 0.4,
    }

    # Performance thresholds (in milliseconds)
    PERFORMANCE_THRESHOLDS = {
        'instant': 100,          # < 100ms
        'fast': 1000,            # < 1 second
        'acceptable': 10000,     # < 10 seconds
        'slow': 30000,           # < 30 seconds
        'very_slow': float('inf'), # > 30 seconds
    }

    def __init__(self):
        """Initialize cost estimator"""
        pass

    def estimate(self, query: str, db_type: str = 'sql_server') -> Dict[str, Any]:
        """
        Estimate query cost and performance
        
        Returns:
        {
            'estimated_rows': int,
            'estimated_duration_ms': int,
            'duration_category': 'instant'|'fast'|'acceptable'|'slow'|'very_slow',
            'io_cost': float,
            'cpu_cost': float,
            'memory_mb': float,
            'parallelizable': bool,
            'risk_level': 'LOW'|'MEDIUM'|'HIGH'|'CRITICAL',
            'optimization_tips': List[str],
            'warnings': List[str],
        }
        """
        # Extract query components
        tables = self._extract_tables(query)
        joins = self._extract_joins(query)
        has_where = self._has_where_clause(query)
        has_index = self._has_index_hint(query)
        has_subquery = query.upper().count("SELECT") > 1
        has_group_by = "GROUP BY" in query.upper()
        has_order_by = "ORDER BY" in query.upper()
        has_distinct = "DISTINCT" in query.upper()

        # Estimate base rows
        base_rows = self._estimate_base_rows(tables, has_where)

        # Apply reduction factors
        rows = base_rows
        if has_where:
            rows = int(rows * 0.1)  # WHERE typically reduces by ~90%
        if has_group_by:
            rows = int(rows * 0.5)  # GROUP BY reduces rows
        if has_distinct:
            rows = int(rows * 0.3)  # DISTINCT significantly reduces

        # Estimate duration based on row count and operations
        duration_ms = self._estimate_duration(
            rows, len(joins), has_subquery, has_group_by, has_order_by, db_type
        )

        # Estimate resource usage
        io_cost = self._estimate_io_cost(rows, tables)
        cpu_cost = self._estimate_cpu_cost(rows, len(joins), has_subquery)
        memory_mb = self._estimate_memory(rows, has_group_by, has_order_by)

        # Determine risk level
        risk_level = self._get_performance_risk(duration_ms, rows)

        # Generate optimization tips
        tips = self._generate_optimization_tips(
            query, tables, has_where, has_index, has_subquery, duration_ms, rows
        )

        # Generate warnings
        warnings = self._generate_warnings(rows, duration_ms, len(joins))

        return {
            'estimated_rows': rows,
            'estimated_duration_ms': int(duration_ms),
            'duration_category': self._get_duration_category(duration_ms),
            'io_cost': round(io_cost, 2),
            'cpu_cost': round(cpu_cost, 2),
            'memory_mb': round(memory_mb, 2),
            'parallelizable': len(joins) <= 2 and not has_subquery,
            'risk_level': risk_level,
            'optimization_tips': tips,
            'warnings': warnings,
        }

    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query"""
        tables = []

        # Match FROM clause
        from_pattern = r"FROM\s+([\w\.\[\]`\"']+)"
        from_matches = re.findall(from_pattern, query, re.IGNORECASE)
        tables.extend(from_matches)

        # Match JOIN clauses
        join_pattern = r"JOIN\s+([\w\.\[\]`\"']+)"
        join_matches = re.findall(join_pattern, query, re.IGNORECASE)
        tables.extend(join_matches)

        # Clean table names (remove brackets, backticks, quotes)
        cleaned_tables = []
        for table in tables:
            clean = table.strip("[]`\"'").lower()
            if clean:
                cleaned_tables.append(clean)

        return cleaned_tables

    def _extract_joins(self, query: str) -> List[str]:
        """Extract JOIN types from query"""
        join_pattern = r"\b(INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+|CROSS\s+)?JOIN\b"
        matches = re.findall(join_pattern, query, re.IGNORECASE)
        return [m.strip() if m else "INNER" for m in matches]

    def _has_where_clause(self, query: str) -> bool:
        """Check if query has WHERE clause"""
        return bool(re.search(r"\bWHERE\b", query, re.IGNORECASE))

    def _has_index_hint(self, query: str) -> bool:
        """Check if query has index hints"""
        hints = ["WITH (NOLOCK)", "USE INDEX", "INDEX HINT", "INDEX FORCE"]
        return any(hint in query.upper() for hint in hints)

    def _estimate_base_rows(self, tables: List[str], has_where: bool) -> int:
        """Estimate base row count from tables"""
        if not tables:
            return 1000  # Default estimate

        total_rows = 0
        for table in tables:
            # Check mock stats first
            stats = self.MOCK_TABLE_STATS.get(table)
            if stats:
                total_rows += stats.row_count
            else:
                # Default estimate for unknown tables
                total_rows += 100000

        return total_rows

    def estimate_with_table_stats(
        self, query: str, table_stats: List[Dict[str, Any]], db_type: str = 'sql_server'
    ) -> Dict[str, Any]:
        """
        Estimate query cost using real table statistics
        
        Args:
            query: SQL query
            table_stats: List of real table stats from database
            db_type: Database type
        """
        # Update mock stats with real stats
        for stat in table_stats:
            table_name = stat.get('name', '').lower()
            self.MOCK_TABLE_STATS[table_name] = TableStats(
                name=table_name,
                row_count=stat.get('row_count', 0),
                avg_row_size_bytes=100,  # Default
            )

        # Run normal estimation
        return self.estimate(query, db_type)

    def _estimate_duration(
        self, rows: int, join_count: int, has_subquery: bool,
        has_group_by: bool, has_order_by: bool, db_type: str
    ) -> float:
        """Estimate query duration in milliseconds"""
        # Base cost per 100K rows: ~100ms
        base_duration = max(10, (rows / 100000) * 100)

        # Add cost for operations
        duration = base_duration

        # JOINs multiply cost
        if join_count > 0:
            duration *= (1 + join_count * 0.5)

        # Subqueries add cost
        if has_subquery:
            duration *= 1.5

        # GROUP BY adds cost
        if has_group_by:
            duration *= 1.3

        # ORDER BY adds cost
        if has_order_by:
            duration *= 1.2

        # Database type adjustments
        db_multipliers = {
            'sql_server': 1.0,
            'postgresql': 1.1,
            'mysql': 1.2,
            'mariadb': 1.2,
        }
        duration *= db_multipliers.get(db_type, 1.0)

        return duration

    def _estimate_io_cost(self, rows: int, tables: List[str]) -> float:
        """Estimate I/O cost"""
        # Rough estimate: 1 page read per 1000 rows
        page_reads = max(1, rows / 1000)
        # Each page read costs ~1ms
        return page_reads * 0.001

    def _estimate_cpu_cost(self, rows: int, join_count: int, has_subquery: bool) -> float:
        """Estimate CPU cost"""
        # Base CPU cost
        cpu = rows * 0.00001

        # Joins increase CPU cost
        cpu *= (1 + join_count * 0.3)

        # Subqueries increase CPU cost
        if has_subquery:
            cpu *= 1.5

        return cpu

    def _estimate_memory(self, rows: int, has_group_by: bool, has_order_by: bool) -> float:
        """Estimate memory usage in MB"""
        # Assume 100 bytes per row
        base_memory = (rows * 100) / (1024 * 1024)

        # GROUP BY needs memory for aggregation
        if has_group_by:
            base_memory *= 2

        # ORDER BY needs memory for sorting
        if has_order_by:
            base_memory *= 1.5

        return base_memory

    def _get_performance_risk(self, duration_ms: int, rows: int) -> str:
        """Determine performance risk level"""
        # Risk based on duration
        if duration_ms > 30000 or rows > 10000000:
            return 'CRITICAL'
        elif duration_ms > 10000 or rows > 1000000:
            return 'HIGH'
        elif duration_ms > 1000 or rows > 100000:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _get_duration_category(self, duration_ms: int) -> str:
        """Get duration category"""
        if duration_ms < self.PERFORMANCE_THRESHOLDS['instant']:
            return 'instant'
        elif duration_ms < self.PERFORMANCE_THRESHOLDS['fast']:
            return 'fast'
        elif duration_ms < self.PERFORMANCE_THRESHOLDS['acceptable']:
            return 'acceptable'
        elif duration_ms < self.PERFORMANCE_THRESHOLDS['slow']:
            return 'slow'
        else:
            return 'very_slow'

    def _generate_optimization_tips(
        self, query: str, tables: List[str], has_where: bool,
        has_index: bool, has_subquery: bool, duration_ms: int, rows: int
    ) -> List[str]:
        """Generate optimization suggestions"""
        tips = []

        # Tip: Add WHERE clause
        if not has_where and rows > 100000:
            tips.append("Add WHERE clause to filter results - full table scan detected")

        # Tip: Use specific columns
        if "SELECT *" in query.upper():
            tips.append("Use specific column names instead of SELECT * - reduces data transfer")

        # Tip: Add index hints
        if not has_index and duration_ms > 5000:
            tips.append("Consider adding index hints or ensuring proper indexes exist")

        # Tip: Avoid subqueries
        if has_subquery and duration_ms > 5000:
            tips.append("Consider rewriting subqueries as JOINs - may be more efficient")

        # Tip: Use LIMIT/TOP
        if duration_ms > 5000 and "LIMIT" not in query.upper() and "TOP" not in query.upper():
            tips.append("Consider using LIMIT/TOP clause to reduce result set")

        # Tip: Batch processing
        if rows > 1000000:
            tips.append("Consider processing data in batches instead of single query")

        # Tip: Test on smaller dataset
        if duration_ms > 10000:
            tips.append("Test on development database first before running on production")

        return tips

    def _generate_warnings(self, rows: int, duration_ms: int, join_count: int) -> List[str]:
        """Generate performance warnings"""
        warnings = []

        if duration_ms > 30000:
            warnings.append(f"Query estimated to take {duration_ms}ms - exceeds 30 second threshold!")

        if rows > 1000000:
            warnings.append(f"Query may return {rows:,} rows - very high data volume")

        if join_count > 3:
            warnings.append(f"Query has {join_count} JOINs - complex joins may impact performance")

        if duration_ms > 10000:
            warnings.append("Estimated duration exceeds 10 seconds - performance degradation risk")

        return warnings
