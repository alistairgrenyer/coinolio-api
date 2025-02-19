from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.base import get_db
from app.core.deps import check_subscription, check_portfolio_limit
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, Portfolio
from app.models.enums import SubscriptionTier
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse
)
from app.schemas.portfolio_sync import (
    SyncRequest, SyncResponse, SyncStatusResponse,
    SyncChange, ChangeType
)
from app.services.sync_manager import SyncManager

router = APIRouter()
sync_manager = SyncManager()

def ensure_timezone_aware(dt: Optional[datetime]) -> datetime:
    """Ensure a datetime is timezone-aware, defaulting to UTC"""
    if dt is None:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(check_portfolio_limit),
) -> Portfolio:
    """Create a new portfolio"""
    portfolio = Portfolio(
        name=portfolio_in.name,
        data=portfolio_in.data,
        user_id=current_user.id,
        version=1,
        is_cloud_synced=True,
        last_sync_at=datetime.now(timezone.utc),
        last_sync_device="web"
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return portfolio

@router.get("", response_model=List[PortfolioResponse])
async def get_portfolios(
    current_user: User = Depends(get_current_user)
) -> List[Portfolio]:
    """Get all portfolios for the current user"""
    return current_user.portfolios

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Portfolio:
    """Get a specific portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return portfolio

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_in: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Portfolio:
    """Update a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    portfolio.name = portfolio_in.name
    if portfolio_in.data:
        portfolio.data = portfolio_in.data
        portfolio.version += 1
        portfolio.last_sync_at = datetime.now(timezone.utc)
        portfolio.last_sync_device = "web"
    
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return portfolio

@router.post("/{portfolio_id}/sync", response_model=SyncResponse)
async def sync_portfolio(
    portfolio_id: int,
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(check_subscription(SubscriptionTier.PREMIUM))
) -> SyncResponse:
    """
    Sync a portfolio from mobile storage to cloud (Premium feature)
    Uses last-write-wins strategy with conflict detection
    """
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Use the sync manager to handle the sync and get changes
    sync_manager = SyncManager()
    
    # First detect changes
    changes = sync_manager.detect_changes(portfolio.data, sync_request.client_data)
    
    # Then perform the sync
    portfolio = sync_manager.merge_portfolios_db(portfolio, sync_request, db)
    
    return SyncResponse(
        success=True,
        version=portfolio.version,
        data=portfolio.data,
        changes=changes,
        last_sync_at=ensure_timezone_aware(portfolio.last_sync_at)
    )

@router.get("/{portfolio_id}/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    portfolio_id: int,
    client_version: int = Query(..., description="Client's current version"),
    device_id: str = Query(..., description="Client device ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(check_subscription(SubscriptionTier.PREMIUM))
) -> SyncStatusResponse:
    """Get sync status and detect if conflicts exist"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Create sync request from query params with timezone-aware datetime
    sync_request = SyncRequest(
        client_version=client_version,
        device_id=device_id,
        client_data=portfolio.data,  # Use current data since we just want status
        last_sync_at=ensure_timezone_aware(portfolio.last_sync_at)
    )
    
    status = sync_manager.get_sync_status(portfolio, sync_request)
    return SyncStatusResponse(**status)
