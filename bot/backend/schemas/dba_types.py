"""
DBA Domain Types for Admin API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatabaseConnectionCreate(BaseModel):
    """Create database connection request"""
    name: str = Field(..., description="Connection name")
    db_type: str = Field(..., description="Database type (postgresql, mysql, sqlserver, etc.)")
    connection_string: str = Field(..., description="Connection string (will be encrypted)")
    description: Optional[str] = Field(None, description="Connection description")
    environment: Optional[str] = Field(None, description="Environment (production, staging, dev)")
    tags: Optional[List[str]] = Field(None, description="Tags for filtering")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")


class DatabaseConnectionUpdate(BaseModel):
    """Update database connection request"""
    name: Optional[str] = None
    db_type: Optional[str] = None
    connection_string: Optional[str] = None  # Will be encrypted if provided
    description: Optional[str] = None
    environment: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None  # active, inactive, error


class DatabaseConnectionResponse(BaseModel):
    """Database connection response (connection_string is excluded by default)"""
    connection_id: str
    name: str
    db_type: str
    description: Optional[str] = None
    environment: Optional[str] = None
    tags: Optional[List[str]] = None
    status: str
    last_tested_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_by: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DatabaseConnectionTestRequest(BaseModel):
    """Test connection request (for testing before creating)"""
    db_type: str = Field(..., description="Database type")
    connection_string: str = Field(..., description="Connection string to test")


class DatabaseConnectionTestResponse(BaseModel):
    """Test connection response"""
    success: bool
    message: str
    connection_info: Optional[Dict[str, Any]] = None

