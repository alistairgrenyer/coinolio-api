from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.base import get_db
from app.core.deps import check_subscription, check_portfolio_limit
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import (
    User, Portfolio, PortfolioVersion,
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, PortfolioVersionResponse
)
from app.schemas.portfolio_sync import (
    SyncRequest, SyncResponse, SyncStatusResponse,
    PortfolioData, SyncMetadata, SyncChange, ChangeType
)
from app.services.sync_manager import SyncManager

router = APIRouter()
sync_manager = SyncManager()

def calculate_portfolio_metrics(data: dict) -> tuple[int, int]:
    """Calculate portfolio metrics from data"""
    total_value = 0
    asset_count = len(data.get("assets", {}))
    # In a real app, you'd fetch current prices and calculate actual value
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
        change_summary=change_summary
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
    total_value, asset_count = calculate_portfolio_metrics(portfolio_in.data.dict())
    
    portfolio = Portfolio(
        name=portfolio_in.name,
        description=portfolio_in.description,
        data=portfolio_in.data.dict(),
        user_id=current_user.id,
        total_value_usd=total_value,
        asset_count=asset_count
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
    if include_versions:
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
    
    if include_versions:
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
    
    # Store old data for change tracking
    old_data = portfolio.data if portfolio_in.data else None
    
    # Update fields
    update_data = portfolio_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'data' and value:
            portfolio.version += 1
            total_value, asset_count = calculate_portfolio_metrics(value.dict())
            portfolio.total_value_usd = total_value
            portfolio.asset_count = asset_count
            portfolio.data = value.dict()
        elif hasattr(portfolio, field):
            setattr(portfolio, field, value)
    
    # Create new version if data was updated
    if portfolio_in.data:
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
    
    return portfolio.versions[offset:offset + limit]

@router.post("/{portfolio_id}/sync", response_model=SyncResponse)
async def sync_portfolio(
    portfolio_id: int,
    sync_request: SyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(lambda: check_subscription("cloud_storage")),
) -> Portfolio:
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
    
    # Get the base version (last synced state)
    base_portfolio_version = db.query(PortfolioVersion).filter(
        PortfolioVersion.portfolio_id == portfolio_id,
        PortfolioVersion.version == sync_request.base_version
    ).first()
    
    if not base_portfolio_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Base version not found. Full sync required."
        )
    
    # Perform three-way merge
    merged_data, had_conflicts = sync_manager.merge_portfolios(
        base=base_portfolio_version.data,
        local=sync_request.local_data.dict(),
        remote=portfolio.data,
        device_id=sync_request.device_id
    )
    
    # If we have conflicts and force is not set, return error
    if had_conflicts and not sync_request.force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicts detected. Set force=true to merge automatically."
        )
    
    # Calculate changes for version history
    changes = sync_manager.detect_changes(portfolio.data, merged_data)
    
    # Convert changes to SyncChange objects
    sync_changes = []
    for asset_id in changes["added_assets"]:
        sync_changes.append(SyncChange(
            type=ChangeType.ADDED,
            asset_id=asset_id,
            new_value=merged_data["assets"][asset_id]
        ))
    for asset_id in changes["removed_assets"]:
        sync_changes.append(SyncChange(
            type=ChangeType.REMOVED,
            asset_id=asset_id,
            old_value=portfolio.data["assets"][asset_id]
        ))
    for asset_id in changes["modified_assets"]:
        sync_changes.append(SyncChange(
            type=ChangeType.MODIFIED,
            asset_id=asset_id,
            old_value=portfolio.data["assets"][asset_id],
            new_value=merged_data["assets"][asset_id]
        ))
    if changes["settings_changed"]:
        sync_changes.append(SyncChange(
            type=ChangeType.SETTINGS_CHANGED,
            old_value=portfolio.data["settings"],
            new_value=merged_data["settings"]
        ))
    
    # Create sync metadata
    sync_metadata = SyncMetadata(
        device_id=sync_request.device_id,
        had_conflicts=had_conflicts,
        base_version=sync_request.base_version,
        changes=sync_changes
    )
    
    # Update portfolio with merged data
    portfolio.version += 1
    portfolio.data = merged_data
    portfolio.is_cloud_synced = True
    portfolio.last_sync_at = datetime.utcnow()
    
    # Calculate new metrics
    total_value, asset_count = calculate_portfolio_metrics(merged_data)
    portfolio.total_value_usd = total_value
    portfolio.asset_count = asset_count
    
    # Create new version with change tracking
    version = PortfolioVersion(
        portfolio_id=portfolio.id,
        version=portfolio.version,
        data=merged_data,
        total_value_usd=total_value,
        asset_count=asset_count,
        change_summary=sync_metadata.dict()
    )
    db.add(version)
    
    # Commit all changes
    db.commit()
    db.refresh(portfolio)
    
    return SyncResponse(
        version=portfolio.version,
        data=PortfolioData.parse_obj(merged_data),
        sync_metadata=sync_metadata,
        is_cloud_synced=portfolio.is_cloud_synced,
        last_sync_at=portfolio.last_sync_at
    )

@router.get("/{portfolio_id}/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
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
    
    last_version = portfolio.versions[0] if portfolio.versions else None
    
    return SyncStatusResponse(
        is_synced=portfolio.is_cloud_synced,
        last_sync=portfolio.last_sync_at,
        current_version=portfolio.version,
        last_sync_device=last_version.change_summary.get("device_id") if last_version else None,
        had_conflicts=last_version.change_summary.get("had_conflicts", False) if last_version else False,
        pending_changes=[
            SyncChange.parse_obj(change)
            for change in (last_version.change_summary.get("changes", []) if last_version else [])
        ]
    )
