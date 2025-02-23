from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid

from app.core.config import get_settings
from app.models.user import User, RefreshToken, TokenData
from app.models.enums import SubscriptionTier, TierPrivileges
from app.repositories.user import user_repository, refresh_token_repository

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate a password hash"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
        """Create a new JWT access token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(db: Session, user: User) -> str:
        """Create a refresh token for a user"""
        token_data = auth_service.create_token_data(user)
        expires_delta = timedelta(
            days=TierPrivileges.get_refresh_token_expire_days(user.subscription_tier)
        )
        refresh_token = auth_service.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )

        expires_at = datetime.now(timezone.utc) + expires_delta
        
        db_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        
        return refresh_token

    @staticmethod
    def verify_refresh_token(db: Session, token: str) -> RefreshToken:
        """Verify a refresh token and return the associated token record"""
        invalid_token_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not token:
            raise invalid_token_exception
        
        token_data = auth_service.get_token_data(token)
        if not token_data:
            raise invalid_token_exception
        
        refresh_token = refresh_token_repository.get_by_token(db, token=token)
        expires_at = refresh_token.expires_at.replace(tzinfo=timezone.utc)
        if not refresh_token or refresh_token.is_revoked or expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return refresh_token

    @staticmethod
    def update_refresh_token(db: Session, old_token: RefreshToken, user: User) -> str:
        """Update the expiration time of a refresh token and replace it with a new one"""
        token_data = auth_service.create_token_data(user)
        expires_delta = timedelta(
            days=TierPrivileges.get_refresh_token_expire_days(user.subscription_tier)
        )
        new_token = auth_service.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        old_token.token = new_token
        old_token.expires_at = datetime.now(timezone.utc) + expires_delta
        db.commit()
        return new_token

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = user_repository.get_by_email(db, email=email)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def get_token_data(token: str) -> Optional[TokenData]:
        """Get data from JWT token"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenData(**payload)
            return token_data
        except JWTError:
            return None

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> User:
        """Get user from token, raising appropriate exceptions if invalid"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            token_data = auth_service.get_token_data(token)
            if token_data is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = user_repository.get_by_email(db, email=token_data.email)
        if user is None:
            raise credentials_exception
        return user

    @staticmethod
    def create_token_data(user: User) -> dict:
        """Create token data dictionary from user"""
        return {
            "sub": user.email,
            "role": user.role,
            "tier": user.subscription_tier,
        }

    @staticmethod
    def get_token_expiry(tier: SubscriptionTier) -> timedelta:
        """Get token expiration time for a subscription tier"""
        return timedelta(minutes=TierPrivileges.get_access_token_expire_minutes(tier))

auth_service = AuthService()
