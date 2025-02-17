from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float, DateTime, Index
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.core.config import get_settings
from tests.utils.db import get_json_type

settings = get_settings()
is_sqlite = settings.SQLALCHEMY_DATABASE_URI.startswith('sqlite')
JSON_TYPE = get_json_type(is_sqlite)

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data = Column(JSON_TYPE, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    total_value_usd = Column(Float, nullable=False, default=0)
    asset_count = Column(Integer, nullable=False, default=0)
    is_cloud_synced = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_device = Column(String, nullable=True)
    had_conflicts = Column(Boolean, nullable=False, default=False)
    pending_changes = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="portfolios")
    versions = relationship("PortfolioVersion", back_populates="portfolio", cascade="all, delete-orphan", order_by="desc(PortfolioVersion.version)")

    __table_args__ = (
        Index('ix_portfolios_user_id_updated_at', 'user_id', 'updated_at'),
        Index('ix_portfolios_total_value', 'total_value_usd'),
    )

class PortfolioVersion(Base):
    __tablename__ = "portfolio_versions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    version = Column(Integer, nullable=False)
    data = Column(JSON_TYPE, nullable=False)
    total_value_usd = Column(Float, nullable=False, default=0)
    asset_count = Column(Integer, nullable=False, default=0)
    change_summary = Column(JSON_TYPE, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    portfolio = relationship("Portfolio", back_populates="versions")

    __table_args__ = (
        Index('ix_portfolio_versions_portfolio_id_version', 'portfolio_id', 'version', unique=True),
    )
