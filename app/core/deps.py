from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
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

def check_subscription(required_tier: SubscriptionTier) -> Callable:
    """Check if user has access to a premium feature"""
    async def check_subscription_inner(current_user: User = Depends(get_current_user)) -> None:
        if current_user.subscription_tier < required_tier:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a {required_tier.value} subscription"
            )
    return check_subscription_inner

async def check_portfolio_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Check if user has reached their portfolio limit"""
    # Get portfolio limit based on subscription tier
    portfolio_limit = {
        SubscriptionTier.FREE: 1,
        SubscriptionTier.PREMIUM: 10
    }.get(current_user.subscription_tier, 1)
    
    # Count user's portfolios
    portfolio_count = len(current_user.portfolios)
    
    if portfolio_count >= portfolio_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached your portfolio limit ({portfolio_limit}). Upgrade to Premium for more portfolios."
        )
