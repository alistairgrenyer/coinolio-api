from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.models.enums import SubscriptionTier, TierPrivileges
from app.models.user import TokenData, User
from app.services.auth import auth_service

settings = get_settings()

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

async def get_token_data(
    token: str = Depends(reusable_oauth2)
) -> Optional[TokenData]:
    """Get data from JWT token without database lookup"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.get_token_data(token)

async def get_current_user(
    token: str = Depends(reusable_oauth2),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth_service.get_user_from_token(db, token)
    return user

async def validate_request_size(request: Request, token_data: Optional[TokenData] = None):
    """Validate request payload size based on token tier"""
    content_length = request.headers.get('content-length')
    if content_length:
        size = int(content_length)
        tier = token_data.subscription_tier if token_data else SubscriptionTier.GUEST
        limits = TierPrivileges.get_rate_limits(tier)
        if size > limits['max_payload_size']:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request payload too large. Maximum size is {limits['max_payload_size'] // 1024}kb"
            )

def check_subscription(required_tiers: set[SubscriptionTier]) -> Callable:
    """Factory for creating subscription tier check dependencies"""
    async def check_subscription_inner(token_data: TokenData = Depends(get_token_data)):
        if not token_data or token_data.subscription_tier not in required_tiers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires one of {', '.join(required_tiers)} subscription"
            )
    return check_subscription_inner
