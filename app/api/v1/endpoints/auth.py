from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.models.enums import TierPrivileges
from app.models.user import Refresh, Token, User, UserCreate, UserResponse
from app.repositories.user import user_repository
from app.services.auth import auth_service

settings = get_settings()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new user"""
    # Check if user exists
    if user_repository.get_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
    user_dict = user_in.model_dump()
    user_dict["hashed_password"] = auth_service.get_password_hash(user_dict.pop("password"))
    return user_repository.create(db, obj_in=user_dict)

@router.post("/login", response_model=Token)
async def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Login for access token"""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(
        minutes=TierPrivileges.get_access_token_expire_minutes(user.subscription_tier)
    )
    token_data = auth_service.create_token_data(user)
    access_token = auth_service.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = auth_service.create_refresh_token(db, user)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh(
    token_in: Refresh,
    db: Session = Depends(get_db)
) -> Any:
    """Get new access token using refresh token"""
    # Verify refresh token
    db_token = auth_service.verify_refresh_token(db, token_in.refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user and create new access token
    user = db_token.user
    access_token_expires = timedelta(
        minutes=TierPrivileges.get_access_token_expire_minutes(user.subscription_tier)
    )
    token_data = auth_service.create_token_data(user)
    access_token = auth_service.create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    refresh_token = auth_service.update_refresh_token(
        db,
        old_token=db_token,
        user=user
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Logout and revoke refresh token"""
    # Verify and revoke refresh token
    db_token = auth_service.verify_refresh_token(db, refresh_token)
    if db_token:
        db_token.is_revoked = True
        db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user"""
    return current_user
