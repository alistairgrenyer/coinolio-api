"""Test cases for the portfolio repository"""
import pytest, approx
from typing import Dict, Any
import json

from app.models.portfolio import Portfolio
from app.models.user import User
from app.repositories.portfolio import portfolio_repository
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate

@pytest.fixture
def test_user(db_session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_portfolio_data() -> Dict[str, Any]:
    """Sample portfolio data that would come from AsyncStorage"""
    return {
        "portfolios": {
            "portfolio1": {
                "name": "My Crypto Portfolio",
                "coins": {
                    "bitcoin": {
                        "amount": "1.5",
                        "transactions": [
                            {
                                "type": "buy",
                                "amount": "1.0",
                                "price": "45000",
                                "date": "2025-01-01T00:00:00Z"
                            }
                        ]
                    }
                }
            }
        }
    }

@pytest.fixture
def test_portfolio_repository_repository(db_session, test_user) -> Portfolio:
    """Create a test portfolio"""
    portfolio = Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        data={"portfolios": {}},
        version=1,
        is_cloud_synced=False
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio

class TestPortfolioRepository:
    """Test cases for PortfolioRepository"""

    def test_create_portfolio(self, db_session, test_user, sample_portfolio_data):
        """Test creating a new portfolio"""
        portfolio_in = {
            "name": "New Portfolio",
            "data": sample_portfolio_data,
            "user_id": test_user.id
        }
        portfolio = portfolio_repository.create(
            db_session,
            obj_in=portfolio_in
        )

        assert portfolio.name == portfolio_in["name"]
        assert portfolio.data == approx(portfolio_in["data"])
        assert portfolio.user_id == portfolio_in["user_id"]
        assert portfolio.version == 1
        assert not portfolio.is_cloud_synced
        assert portfolio.last_sync_at is None
        assert portfolio.last_sync_device is None

    def test_update_portfolio(self, db_session, test_portfolio_repository):
        """Test updating an existing portfolio"""
        new_data = {"portfolios": {"updated": True}}
        portfolio_update = PortfolioUpdate(
            name="Updated Portfolio",
            data=new_data
        )
        
        updated = portfolio_repository.update(
            db_session,
            db_obj=test_portfolio_repository,
            obj_in=portfolio_update
        )

        assert updated.name == "Updated Portfolio"
        assert updated.data == new_data
        assert updated.version == test_portfolio_repository.version
        assert updated.is_cloud_synced == test_portfolio_repository.is_cloud_synced

    def test_get_by_user(self, db_session, test_user, test_portfolio_repository):
        """Test getting portfolios by user"""
        portfolios = portfolio_repository.get_by_user(
            db_session,
            user_id=test_user.id
        )
        
        assert len(portfolios) == 1
        assert portfolios[0].id == test_portfolio_repository.id
        assert portfolios[0].user_id == test_user.id

    def test_get_by_user_with_pagination(self, db_session, test_user, test_portfolio_repository):
        """Test getting portfolios with pagination"""
        # Create another portfolio
        second_portfolio = Portfolio(
            user_id=test_user.id,
            name="Second Portfolio",
            data={"portfolios": {}},
            version=1
        )
        db_session.add(second_portfolio)
        db_session.commit()

        # Test limit
        portfolios = portfolio_repository.get_by_user(
            db_session,
            user_id=test_user.id,
            limit=1
        )
        assert len(portfolios) == 1

        # Test skip
        skipped_portfolios = portfolio_repository.get_by_user(
            db_session,
            user_id=test_user.id,
            skip=1,
            limit=1
        )
        assert len(skipped_portfolios) == 1
        assert skipped_portfolios[0].id != portfolios[0].id

    def test_get_by_user_and_name(self, db_session, test_user, test_portfolio_repository):
        """Test getting a portfolio by user ID and name"""
        portfolio = portfolio_repository.get_by_user_and_name(
            db_session,
            user_id=test_user.id,
            name=test_portfolio_repository.name
        )
        
        assert portfolio is not None
        assert portfolio.id == test_portfolio_repository.id
        assert portfolio.name == test_portfolio_repository.name

    def test_get_by_user_and_name_not_found(self, db_session, test_user):
        """Test getting a non-existent portfolio by name"""
        portfolio = portfolio_repository.get_by_user_and_name(
            db_session,
            user_id=test_user.id,
            name="Non-existent Portfolio"
        )
        assert portfolio is None

    def test_get_unsynced(self, db_session, test_portfolio_repository):
        """Test getting unsynced portfolios"""
        # Initially our test portfolio is unsynced
        unsynced = portfolio_repository.get_unsynced(db_session)
        assert len(unsynced) == 1
        assert unsynced[0].id == test_portfolio_repository.id

        # Mark as synced
        test_portfolio_repository.is_cloud_synced = True
        db_session.commit()

        # Should now be empty
        unsynced = portfolio_repository.get_unsynced(db_session)
        assert len(unsynced) == 0

    def test_get_by_last_sync_device(self, db_session, test_portfolio_repository):
        """Test getting portfolios by last sync device"""
        device_id = "test_device_123"
        
        # Initially should be empty as no device has synced
        device_portfolios = portfolio_repository.get_by_last_sync_device(
            db_session,
            device_id=device_id
        )
        assert len(device_portfolios) == 0

        # Update sync device
        test_portfolio_repository.last_sync_device = device_id
        db_session.commit()

        # Should now find our portfolio
        device_portfolios = portfolio_repository.get_by_last_sync_device(
            db_session,
            device_id=device_id
        )
        assert len(device_portfolios) == 1
        assert device_portfolios[0].id == test_portfolio_repository.id

    def test_count_by_user(self, db_session, test_user, test_portfolio_repository):
        """Test counting portfolios for a user"""
        count = portfolio_repository.count_by_user(
            db_session,
            user_id=test_user.id
        )
        assert count == 1

        # Add another portfolio
        second_portfolio = Portfolio(
            user_id=test_user.id,
            name="Second Portfolio",
            data={"portfolios": {}},
            version=1
        )
        db_session.add(second_portfolio)
        db_session.commit()

        # Count should increase
        count = portfolio_repository.count_by_user(
            db_session,
            user_id=test_user.id
        )
        assert count == 2
