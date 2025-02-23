from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.custom_types import JSONEncodedDict


class Portfolio(Base):
    """
    Portfolio model that stores the mobile app's AsyncStorage data as JSON.
    The data column contains the entire AsyncStorage dump, while metadata fields
    handle synchronization state.
    """
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    
    # Raw AsyncStorage data from mobile app
    data = Column(JSONEncodedDict, nullable=False)
    
    # Sync metadata
    version = Column(Integer, nullable=False, default=1)
    is_cloud_synced = Column(Boolean, nullable=False, default=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_device = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")

    def __init__(self, **kwargs: dict[str, Any]):
        # Ensure timezone awareness for datetime fields
        if kwargs.get("last_sync_at"):
            dt = kwargs["last_sync_at"]
            if isinstance(dt, datetime) and dt.tzinfo is None:
                kwargs["last_sync_at"] = dt.replace(tzinfo=timezone.utc)
        super().__init__(**kwargs)

    def update_sync_status(self, device_id: str):
        """Update sync status with current time and device"""
        self.last_sync_at = datetime.now(timezone.utc)
        self.last_sync_device = device_id
        self.is_cloud_synced = True
        self.version += 1
