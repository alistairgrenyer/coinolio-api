from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator, ConfigDict
from enum import Enum

class AssetTransaction(BaseModel):
    timestamp: datetime
    type: str = Field(..., description="buy, sell, transfer")
    amount: str = Field(..., description="String for precise decimal handling")
    price_usd: str = Field(..., description="String for precise decimal handling")
    notes: Optional[str] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @model_validator(mode='before')
    @classmethod
    def ensure_timezone_aware(cls, values):
        if not isinstance(values, dict):
            return values
        if 'timestamp' in values:
            dt = values['timestamp']
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except ValueError:
                    dt = datetime.fromtimestamp(0, tz=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            values['timestamp'] = dt.astimezone(timezone.utc)
        return values

class AssetDetails(BaseModel):
    amount: str = Field(..., description="String for precise decimal handling")
    cost_basis: str = Field(..., description="Average cost basis in USD")
    notes: Optional[str] = None
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transactions: List[AssetTransaction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @model_validator(mode='before')
    @classmethod
    def ensure_timezone_aware(cls, values):
        if not isinstance(values, dict):
            return values
        if 'last_modified' in values:
            dt = values['last_modified']
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except ValueError:
                    dt = datetime.fromtimestamp(0, tz=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            values['last_modified'] = dt.astimezone(timezone.utc)
        return values

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

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @model_validator(mode='before')
    @classmethod
    def ensure_timezone_aware(cls, values):
        if not isinstance(values, dict):
            return values
        if 'last_price_update' in values and values['last_price_update']:
            dt = values['last_price_update']
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except ValueError:
                    dt = datetime.fromtimestamp(0, tz=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            values['last_price_update'] = dt.astimezone(timezone.utc)
        return values

class PortfolioData(BaseModel):
    """Complete portfolio data structure"""
    assets: Dict[str, AssetDetails] = Field(
        default_factory=dict,
        description="Map of coin_id to asset details"
    )
    settings: PortfolioSettings = Field(default_factory=PortfolioSettings)
    metadata: PortfolioMetadata
    schema_version: str = "1.0.0"

    @model_validator(mode='before')
    @classmethod
    def validate_assets(cls, values):
        """Ensure all assets have required fields"""
        if not isinstance(values, dict):
            return values
        
        assets = values.get('assets', {})
        if not isinstance(assets, dict):
            raise ValueError("Assets must be a dictionary")
            
        for asset_id, asset in assets.items():
            if not isinstance(asset, (dict, AssetDetails)):
                raise ValueError(f"Asset {asset_id} must be an AssetDetails object")
        return values

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

class ChangeType(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"

class SyncChange(BaseModel):
    type: ChangeType
    path: str
    value: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

class SyncRequest(BaseModel):
    client_data: Dict[str, Any]
    last_sync_at: Optional[datetime]
    client_version: int
    device_id: str

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @model_validator(mode='before')
    @classmethod
    def ensure_timezone_aware(cls, values):
        if not isinstance(values, dict):
            return values
        if 'last_sync_at' in values and values['last_sync_at']:
            dt = values['last_sync_at']
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except ValueError:
                    dt = datetime.fromtimestamp(0, tz=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            values['last_sync_at'] = dt.astimezone(timezone.utc)
        return values

class SyncStatusResponse(BaseModel):
    needs_sync: bool
    has_conflicts: bool
    server_version: int
    server_last_sync: Optional[datetime]

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @model_validator(mode='before')
    @classmethod
    def ensure_timezone_aware(cls, values):
        if not isinstance(values, dict):
            return values
        if 'server_last_sync' in values and values['server_last_sync']:
            dt = values['server_last_sync']
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except ValueError:
                    dt = datetime.fromtimestamp(0, tz=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            values['server_last_sync'] = dt.astimezone(timezone.utc)
        return values

class SyncResponse(BaseModel):
    success: bool
    version: int
    data: Optional[Dict[str, Any]] = None
    changes: List[SyncChange] = Field(default_factory=list)
    last_sync_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @model_validator(mode='before')
    @classmethod
    def ensure_timezone_aware(cls, values):
        if not isinstance(values, dict):
            return values
        if 'last_sync_at' in values and values['last_sync_at']:
            dt = values['last_sync_at']
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                except ValueError:
                    dt = datetime.fromtimestamp(0, tz=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            values['last_sync_at'] = dt.astimezone(timezone.utc)
        return values
