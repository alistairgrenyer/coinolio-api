from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    data = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    total_value_usd = Column(Float, nullable=False, default=0)
    asset_count = Column(Integer, nullable=False, default=0)
    is_cloud_synced = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="portfolios")
    versions = relationship("PortfolioVersion", back_populates="portfolio", cascade="all, delete-orphan")

class PortfolioVersion(Base):
    __tablename__ = "portfolio_versions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    total_value_usd = Column(Float, nullable=False, default=0)
    asset_count = Column(Integer, nullable=False, default=0)
    change_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="versions")
