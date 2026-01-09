"""
Query Analysis Entity
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
    """Query analysis entity"""
    
    query: str = Field(..., description="SQL query text")
    query_id: Optional[str] = Field(None, description="Query identifier/hash")
    calls: int = Field(0, description="Number of executions")
    total_time_ms: Optional[float] = Field(None, description="Total execution time in ms")
    mean_time_ms: Optional[float] = Field(None, description="Mean execution time in ms")
    max_time_ms: Optional[float] = Field(None, description="Max execution time in ms")
    min_time_ms: Optional[float] = Field(None, description="Min execution time in ms")
    rows_returned: Optional[int] = Field(None, description="Rows returned")
    rows_examined: Optional[int] = Field(None, description="Rows examined")
    database: Optional[str] = Field(None, description="Database name")
    schema: Optional[str] = Field(None, description="Schema name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryAnalysis":
        """Create QueryAnalysis from dictionary"""
        # Normalize field names from different database systems
        normalized = {
            "query": data.get("query") or data.get("query_text") or data.get("sql_text", ""),
            "query_id": data.get("query_id") or data.get("query_hash"),
            "calls": data.get("calls") or data.get("exec_count") or data.get("execution_count", 0),
            "total_time_ms": cls._normalize_time(
                data.get("total_time") or data.get("total_elapsed_time") or data.get("total_time_ms")
            ),
            "mean_time_ms": cls._normalize_time(
                data.get("mean_time") or data.get("avg_time") or data.get("avg_elapsed_time") or data.get("mean_time_ms")
            ),
            "max_time_ms": cls._normalize_time(
                data.get("max_time") or data.get("max_elapsed_time") or data.get("max_time_ms")
            ),
            "min_time_ms": cls._normalize_time(
                data.get("min_time") or data.get("min_elapsed_time") or data.get("min_time_ms")
            ),
            "rows_returned": data.get("rows_returned") or data.get("rows"),
            "rows_examined": data.get("rows_examined") or data.get("rows_read"),
            "database": data.get("database") or data.get("db"),
            "schema": data.get("schema"),
        }
        return cls(**normalized)
    
    @staticmethod
    def _normalize_time(time_value: Any) -> Optional[float]:
        """Normalize time value to milliseconds"""
        if time_value is None:
            return None
        
        # If already in milliseconds
        if isinstance(time_value, (int, float)):
            # PostgreSQL pg_stat_statements returns time in milliseconds
            # MySQL performance_schema returns in nanoseconds (divide by 1e9 then * 1000)
            # SQL Server returns in microseconds (divide by 1000)
            # Assume values > 1e12 are nanoseconds, > 1e6 are microseconds
            if time_value > 1e12:
                return time_value / 1e6  # nanoseconds to ms
            elif time_value > 1e6:
                return time_value / 1000  # microseconds to ms
            else:
                return float(time_value)
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)
    
    def is_slow(self, threshold_ms: float = 1000.0) -> bool:
        """Check if query is considered slow"""
        if self.mean_time_ms is None:
            return False
        return self.mean_time_ms > threshold_ms

