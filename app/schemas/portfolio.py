from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator

class PortfolioData(BaseModel):
    """Schema for the portfolio data JSON structure"""
    assets: Dict[str, Dict[str, Any]]
    settings: Dict[str, Any]
    metadata: Dict[str, Any]
    schema_version: str = "1.0.0"

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @field_validator("assets")
    @classmethod
    def validate_assets(cls, v):
        if not v:
            raise ValueError("Portfolio must contain at least one asset")
        for asset_id, asset in v.items():
            required_fields = {'amount', 'cost_basis'}
            if not all(field in asset for field in required_fields):
                raise ValueError(f"Asset {asset_id} missing required fields: {required_fields}")
        return v

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v):
        if v != "1.0.0":
            raise ValueError("Unsupported schema version")
        return v

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

class PortfolioCreate(PortfolioBase):
    data: PortfolioData

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[PortfolioData] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

class PortfolioVersionResponse(BaseModel):
    version: int
    data: PortfolioData
    created_at: datetime
    total_value_usd: float
    asset_count: int
    change_summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

class PortfolioResponse(PortfolioBase):
    id: int
    is_cloud_synced: bool
    created_at: datetime
    updated_at: datetime
    version: int
    data: PortfolioData
    total_value_usd: float
    asset_count: int
    last_sync_at: Optional[datetime]
    versions: List[PortfolioVersionResponse] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )
