from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

class AssetTransaction(BaseModel):
    timestamp: datetime
    type: str = Field(..., description="buy, sell, transfer")
    amount: str = Field(..., description="String for precise decimal handling")
    price_usd: str = Field(..., description="String for precise decimal handling")
    notes: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AssetDetails(BaseModel):
    amount: str = Field(..., description="String for precise decimal handling")
    cost_basis: str = Field(..., description="Average cost basis in USD")
    notes: Optional[str] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    transactions: List[AssetTransaction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class PortfolioSettings(BaseModel):
    preferred_currency: str = "usd"
    notification_preferences: Dict[str, Any] = Field(default_factory=dict)
    display_preferences: Dict[str, Any] = Field(default_factory=dict)
    custom_categories: List[str] = Field(default_factory=list)

class PortfolioMetadata(BaseModel):
    last_modified_device: str
    app_version: str
    platform: str = Field(..., description="ios, android, web")
    last_price_update: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class PortfolioData(BaseModel):
    """Complete portfolio data structure"""
    assets: Dict[str, AssetDetails] = Field(
        default_factory=dict,
        description="Map of coin_id to asset details"
    )
    settings: PortfolioSettings = Field(default_factory=PortfolioSettings)
    metadata: PortfolioMetadata
    schema_version: str = "1.0.0"

    @validator('assets')
    def validate_assets(cls, v):
        """Ensure all assets have required fields"""
        for asset_id, asset in v.items():
            if not isinstance(asset, AssetDetails):
                raise ValueError(f"Asset {asset_id} must be an AssetDetails object")
        return v

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    SETTINGS_CHANGED = "settings_changed"

class SyncChange(BaseModel):
    """Represents a change during sync"""
    type: ChangeType
    asset_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SyncMetadata(BaseModel):
    """Metadata about a sync operation"""
    device_id: str
    had_conflicts: bool
    base_version: int
    changes: List[SyncChange]
    sync_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SyncRequest(BaseModel):
    """Request body for portfolio sync"""
    device_id: str = Field(..., description="Unique identifier for the device")
    local_data: PortfolioData
    base_version: int = Field(..., description="Last synced version number")
    force: bool = Field(
        default=False,
        description="Force sync even if conflicts exist"
    )

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SyncResponse(BaseModel):
    """Response body for portfolio sync"""
    version: int
    data: PortfolioData
    sync_metadata: SyncMetadata
    is_cloud_synced: bool
    last_sync_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SyncStatusResponse(BaseModel):
    """Response body for sync status check"""
    is_synced: bool
    last_sync_at: Optional[datetime]
    server_version: int
    last_sync_device: Optional[str] = None
    had_conflicts: bool = False
    pending_changes: int = 0

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class SyncConflict(BaseModel):
    """Represents a sync conflict that needs resolution"""
    asset_id: str
    local_version: AssetDetails
    remote_version: AssetDetails
    base_version: Optional[AssetDetails]
    conflict_type: str = Field(..., description="modify_modify, add_add, modify_delete")

class ConflictResolutionRequest(BaseModel):
    """Request body for resolving conflicts manually"""
    device_id: str
    conflicts: Dict[str, str] = Field(
        ...,
        description="Map of asset_id to chosen version ('local' or 'remote')"
    )
    base_version: int
