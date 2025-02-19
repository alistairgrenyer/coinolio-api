from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class PortfolioBase(BaseModel):
    """Base schema for portfolio data"""
    name: str
    data: Dict[str, Any]

class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio"""
    pass

class PortfolioUpdate(PortfolioBase):
    """Schema for updating an existing portfolio"""
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class PortfolioResponse(PortfolioBase):
    """Schema for portfolio response"""
    id: int
    user_id: int
    version: int
    is_cloud_synced: bool
    last_sync_at: Optional[datetime] = None
    last_sync_device: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )
