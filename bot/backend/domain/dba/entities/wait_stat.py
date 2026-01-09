"""
Wait Stat Entity
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WaitStat(BaseModel):
    """Wait statistics entity"""
    
    wait_event_type: Optional[str] = Field(None, description="Wait event type")
    wait_event: Optional[str] = Field(None, description="Wait event name")
    wait_count: int = Field(0, description="Number of waits")
    total_wait_time_ms: Optional[float] = Field(None, description="Total wait time in ms")
    avg_wait_time_ms: Optional[float] = Field(None, description="Average wait time in ms")
    max_wait_time_ms: Optional[float] = Field(None, description="Max wait time in ms")
    
    database: Optional[str] = Field(None, description="Database name")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WaitStat":
        """Create WaitStat from dictionary"""
        normalized = {
            "wait_event_type": data.get("wait_event_type") or data.get("wait_type") or data.get("waitcategory"),
            "wait_event": data.get("wait_event") or data.get("wait_event_name") or data.get("wait_type"),
            "wait_count": data.get("wait_count") or data.get("count") or data.get("waiting_tasks_count", 0),
            "total_wait_time_ms": cls._normalize_time(
                data.get("total_wait_time") or data.get("total_wait_time_ms") or data.get("wait_time_ms")
            ),
            "avg_wait_time_ms": cls._normalize_time(
                data.get("avg_wait_time") or data.get("avg_wait_time_ms") or data.get("average_wait_time_ms")
            ),
            "max_wait_time_ms": cls._normalize_time(
                data.get("max_wait_time") or data.get("max_wait_time_ms")
            ),
            "database": data.get("database") or data.get("db"),
        }
        return cls(**normalized)
    
    @staticmethod
    def _normalize_time(time_value: Any) -> Optional[float]:
        """Normalize time value to milliseconds"""
        if time_value is None:
            return None
        if isinstance(time_value, (int, float)):
            # Assume already in milliseconds or convert from microseconds
            if time_value > 1e6:
                return time_value / 1000  # microseconds to ms
            return float(time_value)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)

