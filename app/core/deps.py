from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import get_db
from app.models.enums import SubscriptionTier, TierPrivileges
from app.core.rate_limit import rate_limiter

settings = get_settings()

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

class TokenData:
    """Class to hold token data"""
    def __init__(self, payload: dict):
        self.email = payload.get("sub")
        self.tier = payload.get("tier", SubscriptionTier.GUEST)
        self.portfolio_limit = payload.get("portfolio_limit", 0)
        self.historical_days = payload.get("historical_days", 7)

async def get_token_data(
    token: str = Depends(reusable_oauth2)
) -> Optional[TokenData]:
    """Get data from JWT token without database lookup"""
    if not token:
        return None
        
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return TokenData(payload)
    except JWTError:
        return None

async def get_current_token_data(
    token_data: Optional[TokenData] = Depends(get_token_data),
) -> Optional[TokenData]:
    """Get current token data, ensuring it's valid"""
    if not token_data or not token_data.email:
        return None
    return token_data

def get_portfolio_limit(token_data: Optional[TokenData] = None) -> int:
    """Get the portfolio limit from token data"""
    if not token_data:
        return TierPrivileges.get_portfolio_limit(SubscriptionTier.GUEST)
    return token_data.portfolio_limit

async def validate_request_size(request: Request, token_data: Optional[TokenData] = None):
    """Validate request payload size based on token tier"""
    content_length = request.headers.get('content-length')
    if content_length:
        size = int(content_length)
        tier = token_data.tier if token_data else SubscriptionTier.GUEST
        limits = TierPrivileges.get_rate_limits(tier)
        if size > limits['max_payload_size']:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request payload too large. Maximum size is {limits['max_payload_size'] // 1024}kb"
            )

async def check_portfolio_limit_usage(
    token_data: TokenData = Depends(get_current_token_data),
    portfolio_count: int = None,
) -> None:
    """Check if user has reached their portfolio limit"""
    if portfolio_count is None:
        # If portfolio count not provided, we need to get it from the database
        db = next(get_db())
        try:
            from app.models.user import User
            user = User.get_by_email(db, token_data.email)
            portfolio_count = len(user.portfolios)
        finally:
            db.close()
    
    if portfolio_count >= token_data.portfolio_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Portfolio limit reached. Your subscription tier allows {token_data.portfolio_limit} portfolios."
        )

def require_auth(token_data: TokenData = Depends(get_current_token_data)):
    """Dependency to require authentication"""
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

def check_subscription(required_tier: SubscriptionTier):
    """Factory for creating subscription tier check dependencies"""
    async def check_subscription_inner(token_data: TokenData = Depends(get_current_token_data)):
        if not token_data or token_data.tier != required_tier:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires {required_tier} subscription"
            )
    return check_subscription_inner

async def check_rate_limit(
    request: Request,
    token_data: Optional[TokenData] = Depends(get_current_token_data)
):
    """Check rate limit for public endpoints"""
    await rate_limiter.check_rate_limit(request, is_authenticated=token_data is not None)
