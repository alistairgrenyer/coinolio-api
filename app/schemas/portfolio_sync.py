from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def ensure_timezone_aware(values: dict, key: str) -> dict:
    if not isinstance(values, dict):
        return values
    if key in values:
        dt = values[key]
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                dt = datetime.fromtimestamp(0, tz=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        values[key] = dt.astimezone(timezone.utc)
    return values

class ChangeType(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"

class SyncChange(BaseModel):
    type: ChangeType
    path: str
    value: Optional[dict[str, Any]] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

class SyncRequest(BaseModel):
    client_data: dict[str, Any]
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
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        return ensure_timezone_aware(values, 'last_sync_at')

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
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        return ensure_timezone_aware(values, 'server_last_sync')

class SyncResponse(BaseModel):
    success: bool
    version: int
    data: Optional[dict[str, Any]] = None
    changes: list[SyncChange] = Field(default_factory=list)
    last_sync_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

    @model_validator(mode='before')
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        return ensure_timezone_aware(values, 'last_sync_at')
