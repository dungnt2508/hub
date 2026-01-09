"""
Incident Entity
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    """Incident types"""
    SLOW_QUERY = "slow_query"
    BLOCKING = "blocking"
    DEADLOCK = "deadlock"
    CONNECTION_POOL_EXHAUSTED = "connection_pool_exhausted"
    DISK_SPACE = "disk_space"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_PRESSURE = "cpu_pressure"
    REPLICATION_LAG = "replication_lag"
    OTHER = "other"


class IncidentStatus(str, Enum):
    """Incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(BaseModel):
    """Database incident entity"""
    
    incident_id: Optional[str] = Field(None, description="Incident ID")
    incident_type: IncidentType = Field(..., description="Incident type")
    severity: IncidentSeverity = Field(..., description="Severity level")
    status: IncidentStatus = Field(IncidentStatus.OPEN, description="Status")
    
    title: str = Field(..., description="Incident title")
    description: Optional[str] = Field(None, description="Incident description")
    
    database: Optional[str] = Field(None, description="Database name")
    affected_tables: Optional[List[str]] = Field(None, description="Affected tables")
    
    # Related data
    related_queries: Optional[List[str]] = Field(None, description="Related query IDs")
    related_sessions: Optional[List[int]] = Field(None, description="Related session IDs")
    
    # Timestamps
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    # Resolution
    resolution: Optional[str] = Field(None, description="Resolution description")
    resolved_by: Optional[str] = Field(None, description="Resolved by user")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Incident":
        """Create Incident from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)
    
    def is_open(self) -> bool:
        """Check if incident is open"""
        return self.status in [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]
    
    def is_critical(self) -> bool:
        """Check if incident is critical"""
        return self.severity == IncidentSeverity.CRITICAL

