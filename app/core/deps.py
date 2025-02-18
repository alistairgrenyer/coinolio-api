from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from fastapi.security import OAuth2PasswordBearer

from app.db.base import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.enums import UserRole, SubscriptionTier
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

async def check_subscription(
    feature: str,
    current_user: User = Depends(get_current_user)
) -> None:
    """Check if user has access to a premium feature"""
    if current_user.subscription_tier != SubscriptionTier.PREMIUM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This feature requires a premium subscription"
        )
    
    if current_user.subscription_expires_at and current_user.subscription_expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Your subscription has expired"
        )

async def check_portfolio_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Check if user has reached their portfolio limit"""
    portfolio_count = len(current_user.portfolios)
    max_portfolios = 10 if current_user.subscription_tier == SubscriptionTier.PREMIUM else 3
    
    if portfolio_count >= max_portfolios:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached your limit of {max_portfolios} portfolios"
        )
