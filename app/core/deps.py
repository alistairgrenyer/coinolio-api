from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

from app.db.base import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.enums import UserRole, SubscriptionTier, TIER_LIMITS
from app.core.rate_limit import rate_limiter

# Make token optional by setting auto_error=False
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/token", auto_error=False)

async def get_optional_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if token:
        return await get_current_user(token, db)
    return None

async def check_rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Check rate limit for public endpoints"""
    await rate_limiter.check_rate_limit(request, is_authenticated=current_user is not None)

def check_admin(current_user: User = Depends(get_current_user)) -> User:
    """Check if the current user is an admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def check_subscription(
    feature: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Check if user has access to a specific feature based on their subscription"""
    
    # Check if subscription has expired
    if (current_user.subscription_tier == SubscriptionTier.PREMIUM and 
        current_user.subscription_expires_at and 
        current_user.subscription_expires_at < datetime.utcnow()):
        # Downgrade to free tier if premium subscription expired
        current_user.subscription_tier = SubscriptionTier.FREE
        db.commit()
    
    tier_limits = TIER_LIMITS[current_user.subscription_tier]
    
    if not tier_limits.get(feature, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires a premium subscription"
        )

def check_portfolio_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Check if user has reached their portfolio limit"""
    tier_limits = TIER_LIMITS[current_user.subscription_tier]
    current_portfolios = len(current_user.portfolios)
    
    if current_portfolios >= tier_limits["max_portfolios"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have reached your portfolio limit. Upgrade to premium for unlimited portfolios."
        )
