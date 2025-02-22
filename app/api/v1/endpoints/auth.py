from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.config import get_settings
from app.core.deps import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User, UserCreate, UserResponse, Token, RefreshToken
from app.models.enums import TierPrivileges
import uuid

settings = get_settings()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_refresh_token(db: Session, user: User) -> str:
    """Create a refresh token for a user"""
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=TierPrivileges.get_refresh_token_expire_days(user.subscription_tier)
    )
    
    db_token = RefreshToken(
        token=token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()
    
    return token

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new user"""
    if get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = create_user(db, user_in)
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """Login to get access token"""
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get expiration time based on user's tier
    expires_delta = timedelta(minutes=TierPrivileges.get_access_token_expire_minutes(user.subscription_tier))
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.email,
            "tier": user.subscription_tier,
            "portfolio_limit": TierPrivileges.get_portfolio_limit(user.subscription_tier),
            "historical_days": TierPrivileges.get_historical_data_days(user.subscription_tier)
        },
        expires_delta=expires_delta
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(db, user)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Form(...),
    db: Session = Depends(get_db)
) -> Any:
    """Get new access token using refresh token"""
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=TierPrivileges.get_access_token_expire_minutes(db_token.user.subscription_tier))
    access_token = create_access_token(
        data={
            "sub": db_token.user.email,
            "tier": db_token.user.subscription_tier,
            "portfolio_limit": TierPrivileges.get_portfolio_limit(db_token.user.subscription_tier),
            "historical_days": TierPrivileges.get_historical_data_days(db_token.user.subscription_tier)
        },
        expires_delta=access_token_expires
    )
    
    # Create new refresh token and revoke old one
    db_token.is_revoked = True
    new_refresh_token = create_refresh_token(db, db_token.user)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user information"""
    return current_user
