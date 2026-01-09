"""
Capacity Forecast Entity
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class CapacityForecast(BaseModel):
    """Capacity forecast entity"""
    
    database: str = Field(..., description="Database name")
    metric_name: str = Field(..., description="Metric name (size, connections, etc.)")
    current_value: float = Field(..., description="Current value")
    unit: str = Field("bytes", description="Unit of measurement")
    
    # Forecast data
    forecast_date: datetime = Field(..., description="Forecast date")
    forecasted_value: float = Field(..., description="Forecasted value")
    growth_rate_percent: Optional[float] = Field(None, description="Growth rate percentage")
    
    # Thresholds
    warning_threshold: Optional[float] = Field(None, description="Warning threshold")
    critical_threshold: Optional[float] = Field(None, description="Critical threshold")
    
    # Status
    status: str = Field("ok", description="Status: ok, warning, critical")
    recommendation: Optional[str] = Field(None, description="Recommendation")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Forecast timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapacityForecast":
        """Create CapacityForecast from dictionary"""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict(exclude_none=True)
    
    def is_warning(self) -> bool:
        """Check if forecast is in warning state"""
        if self.warning_threshold is None:
            return False
        return self.forecasted_value >= self.warning_threshold
    
    def is_critical(self) -> bool:
        """Check if forecast is in critical state"""
        if self.critical_threshold is None:
            return False
        return self.forecasted_value >= self.critical_threshold

