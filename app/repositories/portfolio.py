from typing import Optional

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio, Portfolio, Portfolio]):
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Portfolio]:
        """Get all portfolios for a user"""
        return (
            db.query(Portfolio)
            .filter(Portfolio.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_user_and_name(
        self, db: Session, *, user_id: int, name: str
    ) -> Optional[Portfolio]:
        """Get a portfolio by user ID and name"""
        return (
            db.query(Portfolio)
            .filter(Portfolio.user_id == user_id, Portfolio.name == name)
            .first()
        )
    
    def get_unsynced(self, db: Session, *, skip: int = 0, limit: int = 100) -> list[Portfolio]:
        """Get portfolios that haven't been synced to the cloud"""
        return (
            db.query(Portfolio)
            .filter(Portfolio.is_cloud_synced == False)  # noqa: E712
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_last_sync_device(
        self, db: Session, *, device_id: str, skip: int = 0, limit: int = 100
    ) -> list[Portfolio]:
        """Get portfolios last synced from a specific device"""
        return (
            db.query(Portfolio)
            .filter(Portfolio.last_sync_device == device_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def count_by_user(self, db: Session, *, user_id: int) -> int:
        """Count the number of portfolios for a user"""
        return (
            db.query(Portfolio)
            .filter(Portfolio.user_id == user_id)
            .count()
        )

# Create repository instance
portfolio_repository = PortfolioRepository(Portfolio)
