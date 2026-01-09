"""
Blocking Session Entity
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BlockingSession(BaseModel):
    """Blocking session entity"""
    
    blocked_pid: Optional[int] = Field(None, description="Blocked process ID")
    blocked_session_id: Optional[int] = Field(None, description="Blocked session ID")
    blocked_query: Optional[str] = Field(None, description="Blocked query text")
    blocked_duration_ms: Optional[float] = Field(None, description="Block duration in ms")
    
    blocking_pid: Optional[int] = Field(None, description="Blocking process ID")
    blocking_session_id: Optional[int] = Field(None, description="Blocking session ID")
    blocking_query: Optional[str] = Field(None, description="Blocking query text")
    blocking_duration_ms: Optional[float] = Field(None, description="Blocking query duration in ms")
    
    lock_type: Optional[str] = Field(None, description="Lock type")
    lock_mode: Optional[str] = Field(None, description="Lock mode")
    database: Optional[str] = Field(None, description="Database name")
    table: Optional[str] = Field(None, description="Table name")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlockingSession":
        """Create BlockingSession from dictionary"""
        normalized = {
            "blocked_pid": data.get("blocked_pid") or data.get("blocked_process_id"),
            "blocked_session_id": data.get("blocked_session_id") or data.get("blocked_spid"),
            "blocked_query": data.get("blocked_query") or data.get("blocked_sql"),
            "blocked_duration_ms": cls._normalize_time(
                data.get("blocked_duration") or data.get("blocked_duration_ms") or data.get("wait_time_ms")
            ),
            "blocking_pid": data.get("blocking_pid") or data.get("blocking_process_id"),
            "blocking_session_id": data.get("blocking_session_id") or data.get("blocking_spid"),
            "blocking_query": data.get("blocking_query") or data.get("blocking_sql"),
            "blocking_duration_ms": cls._normalize_time(
                data.get("blocking_duration") or data.get("blocking_duration_ms")
            ),
            "lock_type": data.get("lock_type") or data.get("locktype"),
            "lock_mode": data.get("lock_mode") or data.get("mode"),
            "database": data.get("database") or data.get("db") or data.get("database_name"),
            "table": data.get("table") or data.get("tablename") or data.get("table_name"),
        }
        return cls(**normalized)
    
    @staticmethod
    def _normalize_time(time_value: Any) -> Optional[float]:
        """Normalize time value to milliseconds"""
        if time_value is None:
            return None
        if isinstance(time_value, (int, float)):
            # Assume already in milliseconds or convert from seconds
            if time_value < 1000:
                return time_value * 1000  # seconds to ms
            return float(time_value)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)
    
    def is_critical(self, threshold_ms: float = 5000.0) -> bool:
        """Check if blocking is critical (blocked for too long)"""
        if self.blocked_duration_ms is None:
            return False
        return self.blocked_duration_ms > threshold_ms

