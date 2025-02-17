from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, validator
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import UserRole, SubscriptionTier
from app.core.config import get_settings
from tests.utils.db import get_json_type

settings = get_settings()
is_sqlite = settings.SQLALCHEMY_DATABASE_URI.startswith('sqlite')
JSON_TYPE = get_json_type(is_sqlite)

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Role and subscription
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, unique=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String, nullable=True)
    is_cloud_synced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Store the portfolio data as JSON
    data = Column(JSON_TYPE, nullable=False)
    
    # Metadata for analytics
    total_value_usd = Column(Integer)  # Stored in cents for precision
    asset_count = Column(Integer)
    last_sync_at = Column(DateTime)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    versions = relationship("PortfolioVersion", back_populates="portfolio", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_portfolios_user_id_updated_at', 'user_id', 'updated_at'),
        Index('ix_portfolios_total_value', 'total_value_usd'),
    )

class PortfolioVersion(Base):
    __tablename__ = "portfolio_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer, nullable=False)
    data = Column(JSON_TYPE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_value_usd = Column(Integer)
    asset_count = Column(Integer)
    change_summary = Column(JSON_TYPE)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    
    portfolio = relationship("Portfolio", back_populates="versions")
    
    __table_args__ = (
        Index('ix_portfolio_versions_portfolio_id_version', 'portfolio_id', 'version', unique=True),
    )

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="refresh_tokens")

# Pydantic Models
class PortfolioData(BaseModel):
    """Schema for the portfolio data JSON structure"""
    assets: Dict[str, Dict[str, Any]]
    settings: Dict[str, Any]
    metadata: Dict[str, Any]
    schema_version: str = "1.0.0"

    model_config = ConfigDict(from_attributes=True)

    @field_validator("assets")
    @classmethod
    def validate_assets(cls, v):
        if not v:
            raise ValueError("Portfolio must contain at least one asset")
        return v

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PortfolioCreate(PortfolioBase):
    data: PortfolioData

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[PortfolioData] = None

    model_config = ConfigDict(from_attributes=True)

class PortfolioVersionResponse(BaseModel):
    version: int
    data: PortfolioData
    created_at: datetime
    total_value_usd: float
    asset_count: int
    change_summary: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    role: UserRole
    subscription_tier: SubscriptionTier
    subscription_expires_at: Optional[datetime] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    portfolios: List[PortfolioResponse] = []

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    subscription_tier: Optional[SubscriptionTier] = None

    model_config = ConfigDict(from_attributes=True)
