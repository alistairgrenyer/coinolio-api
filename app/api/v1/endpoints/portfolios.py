from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.base import get_db
from app.core.deps import check_subscription, check_portfolio_limit
from app.api.v1.endpoints.auth import get_current_user
from app.models import User, Portfolio, PortfolioVersion
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioVersionResponse, PortfolioData
)
from app.schemas.portfolio_sync import (
    SyncRequest, SyncResponse, SyncStatusResponse,
    SyncMetadata, SyncChange, ChangeType
)
from app.services.sync_manager import SyncManager

router = APIRouter()
sync_manager = SyncManager()

def calculate_portfolio_metrics(data: dict) -> tuple[float, int]:
    """Calculate portfolio metrics from data"""
    total_value = 0.0
    assets = data.get("assets", {})
    asset_count = len(assets)
    
    # Calculate total value
    for asset in assets.values():
        amount = float(asset.get("amount", 0))
        cost_basis = float(asset.get("cost_basis", 0))
        total_value += amount * cost_basis
    
    return total_value, asset_count

def create_portfolio_version(
    db: Session,
    portfolio: Portfolio,
    old_data: Optional[dict] = None
) -> PortfolioVersion:
    """Create a new version of the portfolio"""
    total_value, asset_count = calculate_portfolio_metrics(portfolio.data)
    
    # Calculate what changed from the previous version
    change_summary = None
    if old_data:
        change_summary = {
            "added_assets": [
                asset_id for asset_id in portfolio.data["assets"]
                if asset_id not in old_data["assets"]
            ],
            "removed_assets": [
                asset_id for asset_id in old_data["assets"]
                if asset_id not in portfolio.data["assets"]
            ],
            "modified_assets": [
                asset_id for asset_id in portfolio.data["assets"]
                if asset_id in old_data["assets"]
                and portfolio.data["assets"][asset_id] != old_data["assets"][asset_id]
            ]
        }
    
    version = PortfolioVersion(
        portfolio_id=portfolio.id,
        version=portfolio.version,
        data=portfolio.data,
        total_value_usd=total_value,
        asset_count=asset_count,
        change_summary=change_summary,
        created_at=datetime.now(timezone.utc)
    )
    db.add(version)
    return version

@router.post("", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(check_portfolio_limit),
) -> Portfolio:
    """Create a new portfolio"""
    portfolio_data = portfolio_in.data.model_dump()
    total_value, asset_count = calculate_portfolio_metrics(portfolio_data)
    
    portfolio = Portfolio(
        name=portfolio_in.name,
        description=portfolio_in.description,
        data=portfolio_data,
        user_id=current_user.id,
        total_value_usd=total_value,
        asset_count=asset_count,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(portfolio)
    db.commit()
    
    # Create initial version
    create_portfolio_version(db, portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return portfolio

@router.get("", response_model=List[PortfolioResponse])
async def get_portfolios(
    current_user: User = Depends(get_current_user),
    include_versions: bool = Query(False, description="Include version history"),
    limit_versions: int = Query(5, description="Number of versions to include")
) -> List[Portfolio]:
    """Get all portfolios for the current user"""
    portfolios = current_user.portfolios
    if not include_versions:
        for portfolio in portfolios:
            portfolio.versions = []
    elif limit_versions:
        for portfolio in portfolios:
            portfolio.versions = portfolio.versions[:limit_versions]
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_versions: bool = Query(False, description="Include version history"),
    limit_versions: int = Query(5, description="Number of versions to include")
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
    
    if not include_versions:
        portfolio.versions = []
    else:
        portfolio.versions = portfolio.versions[:limit_versions]
    
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
    
    # Store old data for version tracking
    old_data = portfolio.data.copy()
    
    # Update fields
    if portfolio_in.name is not None:
        portfolio.name = portfolio_in.name
    if portfolio_in.description is not None:
        portfolio.description = portfolio_in.description
    if portfolio_in.data is not None:
        portfolio.data = portfolio_in.data.model_dump()
        total_value, asset_count = calculate_portfolio_metrics(portfolio.data)
        portfolio.total_value_usd = total_value
        portfolio.asset_count = asset_count
    
    # Increment version and update timestamp
    portfolio.version += 1
    portfolio.updated_at = datetime.now(timezone.utc)
    
    # Create new version
    create_portfolio_version(db, portfolio, old_data)
    
    db.commit()
    db.refresh(portfolio)
    return portfolio

@router.get("/{portfolio_id}/versions", response_model=List[PortfolioVersionResponse])
async def get_portfolio_versions(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, description="Number of versions to return"),
    offset: int = Query(0, description="Offset for pagination")
) -> List[PortfolioVersion]:
    """Get version history for a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    versions = db.query(PortfolioVersion).filter(
        PortfolioVersion.portfolio_id == portfolio_id
    ).order_by(
        PortfolioVersion.version.desc()
    ).offset(offset).limit(limit).all()
    
    return versions

@router.post("/{portfolio_id}/sync", response_model=SyncResponse)
async def sync_portfolio(
    portfolio_id: int,
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(lambda: check_subscription("cloud_storage")),
) -> SyncResponse:
    """
    Sync a portfolio from mobile storage to cloud (Premium feature)
    Handles conflict resolution using three-way merge
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
    
    # Get the sync status first
    sync_status = sync_manager.get_sync_status(portfolio, sync_request)
    
    # If there are conflicts, return them
    if sync_status.has_conflicts:
        return SyncResponse(
            status="CONFLICT",
            conflicts=sync_status.conflicts,
            server_version=portfolio.version
        )
    
    # No conflicts, safe to sync
    old_data = portfolio.data.copy()
    portfolio.data = sync_request.client_data
    portfolio.version += 1
    portfolio.is_cloud_synced = True
    portfolio.last_sync_at = datetime.now(timezone.utc)
    portfolio.updated_at = datetime.now(timezone.utc)
    
    # Update metrics
    total_value, asset_count = calculate_portfolio_metrics(portfolio.data)
    portfolio.total_value_usd = total_value
    portfolio.asset_count = asset_count
    
    # Create new version
    create_portfolio_version(db, portfolio, old_data)
    
    db.commit()
    db.refresh(portfolio)
    
    return SyncResponse(
        status="SUCCESS",
        server_version=portfolio.version,
        server_data=portfolio.data
    )

@router.get("/{portfolio_id}/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    
    return SyncStatusResponse(
        is_synced=portfolio.is_cloud_synced,
        last_sync_at=portfolio.last_sync_at,
        server_version=portfolio.version,
        last_sync_device=portfolio.last_sync_device,
        had_conflicts=portfolio.had_conflicts,
        pending_changes=portfolio.pending_changes
    )
