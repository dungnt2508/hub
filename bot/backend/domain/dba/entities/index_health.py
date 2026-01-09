"""
Index Health Entity
"""
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class IndexHealthStatus(str, Enum):
    """Index health status"""
    HEALTHY = "healthy"
    UNUSED = "unused"
    DUPLICATE = "duplicate"
    MISSING = "missing"
    FRAGMENTED = "fragmented"


class IndexHealth(BaseModel):
    """Index health entity"""
    
    index_name: str = Field(..., description="Index name")
    table_name: str = Field(..., description="Table name")
    schema_name: Optional[str] = Field(None, description="Schema name")
    database_name: Optional[str] = Field(None, description="Database name")
    
    # Usage statistics
    index_scans: int = Field(0, description="Number of index scans")
    index_tuples_read: Optional[int] = Field(None, description="Index tuples read")
    index_tuples_fetched: Optional[int] = Field(None, description="Index tuples fetched")
    
    # Size statistics
    index_size_bytes: Optional[int] = Field(None, description="Index size in bytes")
    table_size_bytes: Optional[int] = Field(None, description="Table size in bytes")
    
    # Health metrics
    health_status: IndexHealthStatus = Field(IndexHealthStatus.HEALTHY, description="Health status")
    fragmentation_percent: Optional[float] = Field(None, description="Fragmentation percentage")
    last_used: Optional[str] = Field(None, description="Last used timestamp")
    
    # Recommendations
    recommendation: Optional[str] = Field(None, description="Recommendation")
    
    class Config:
        use_enum_values = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndexHealth":
        """Create IndexHealth from dictionary"""
        # Normalize field names
        normalized = {
            "index_name": data.get("indexname") or data.get("index_name") or data.get("name", ""),
            "table_name": data.get("tablename") or data.get("table_name") or data.get("table", ""),
            "schema_name": data.get("schemaname") or data.get("schema_name") or data.get("schema"),
            "database_name": data.get("database_name") or data.get("database") or data.get("db"),
            "index_scans": data.get("idx_scan") or data.get("index_scans") or data.get("scans", 0),
            "index_tuples_read": data.get("idx_tup_read") or data.get("index_tuples_read") or data.get("tuples_read"),
            "index_tuples_fetched": data.get("idx_tup_fetch") or data.get("index_tuples_fetched") or data.get("tuples_fetched"),
            "index_size_bytes": data.get("index_size") or data.get("index_size_bytes") or data.get("size_bytes"),
            "table_size_bytes": data.get("table_size") or data.get("table_size_bytes"),
            "fragmentation_percent": data.get("fragmentation") or data.get("fragmentation_percent"),
            "last_used": data.get("last_used") or data.get("last_scan"),
        }
        
        # Determine health status
        health_status = IndexHealthStatus.HEALTHY
        recommendation = None
        
        if normalized["index_scans"] < 10:
            health_status = IndexHealthStatus.UNUSED
            recommendation = "Index rarely used, consider removing"
        elif normalized.get("fragmentation_percent", 0) > 30:
            health_status = IndexHealthStatus.FRAGMENTED
            recommendation = "Index fragmented, consider rebuilding"
        
        normalized["health_status"] = health_status
        normalized["recommendation"] = recommendation
        
        return cls(**normalized)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)
    
    def is_unhealthy(self) -> bool:
        """Check if index is unhealthy"""
        return self.health_status != IndexHealthStatus.HEALTHY

