import pytest
from fastapi import status
from datetime import datetime, timezone
from copy import deepcopy

from app.core.config import get_settings
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioVersion
from app.models.enums import SubscriptionTier
from tests.factories.portfolio import PortfolioFactory, PortfolioVersionFactory

settings = get_settings()

def create_portfolio_data(with_metadata: bool = True) -> dict:
    """Create test portfolio data"""
    data = {
        "name": "Test Portfolio",
        "description": "My test portfolio",
        "data": {
            "assets": {
                "bitcoin": {
                    "amount": "1.5",
                    "cost_basis": "35000.00",
                    "notes": "Initial investment"
                }
            },
            "settings": {
                "default_currency": "USD",
                "price_alerts": True
            },
            "metadata": {},
            "schema_version": "1.0.0"
        }
    }
    if with_metadata:
        data["data"]["metadata"].update({
            "created_from": "web",
            "last_modified": datetime.now(timezone.utc).isoformat()
        })
    return data

class TestPortfolioEndpoints:
    def test_create_portfolio_success(self, authorized_client, test_user):
        """Test successful portfolio creation"""
        portfolio_data = create_portfolio_data()
        
        response = authorized_client.post(
            f"{settings.API_V1_STR}/portfolios/",
            json=portfolio_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == portfolio_data["name"]
        assert data["description"] == portfolio_data["description"]
        assert data["data"]["assets"] == portfolio_data["data"]["assets"]
        assert "id" in data
        assert data["version"] == 1
        assert data["asset_count"] == 1

    def test_create_portfolio_invalid_data(self, authorized_client):
        """Test portfolio creation with invalid data"""
        # Missing required assets field
        portfolio_data = create_portfolio_data(with_metadata=False)
        portfolio_data["data"].pop("assets")
        
        response = authorized_client.post(
            f"{settings.API_V1_STR}/portfolios/",
            json=portfolio_data
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_portfolios(self, authorized_client, test_user, db_session):
        """Test getting all portfolios for a user"""
        # Create some test portfolios
        portfolios = [
            PortfolioFactory(user_id=test_user["id"]),
            PortfolioFactory(user_id=test_user["id"])
        ]
        for portfolio in portfolios:
            db_session.add(portfolio)
            db_session.flush()  # Ensure IDs are generated
        db_session.commit()

        response = authorized_client.get(f"{settings.API_V1_STR}/portfolios/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert any(p["name"] == portfolios[0].name for p in data)
        assert any(p["name"] == portfolios[1].name for p in data)

    def test_get_portfolio_by_id(self, authorized_client, test_user, db_session):
        """Test getting a specific portfolio"""
        portfolio = PortfolioFactory(user_id=test_user["id"])
        db_session.add(portfolio)
        db_session.flush()  # Ensure ID is generated
        db_session.commit()

        response = authorized_client.get(
            f"{settings.API_V1_STR}/portfolios/{portfolio.id}"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == portfolio.id
        assert data["name"] == portfolio.name
        assert data["data"] == portfolio.data

    def test_get_portfolio_not_found(self, authorized_client):
        """Test getting a non-existent portfolio"""
        response = authorized_client.get(
            f"{settings.API_V1_STR}/portfolios/999999"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_portfolio(self, authorized_client, test_user, db_session):
        """Test updating a portfolio"""
        portfolio = PortfolioFactory(user_id=test_user["id"])
        db_session.add(portfolio)
        db_session.flush()  # Ensure ID is generated
        db_session.commit()

        update_data = {
            "name": "Updated Portfolio",
            "description": "Updated description",
            "data": {
                "assets": {
                    "bitcoin": {
                        "amount": "2.0",
                        "cost_basis": "40000.00"
                    },
                    "ethereum": {
                        "amount": "10.0",
                        "cost_basis": "2500.00"
                    }
                },
                "settings": {"default_currency": "USD"},
                "metadata": {
                    "last_modified": datetime.now(timezone.utc).isoformat()
                },
                "schema_version": "1.0.0"
            }
        }

        response = authorized_client.put(
            f"{settings.API_V1_STR}/portfolios/{portfolio.id}",
            json=update_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["data"]["assets"] == update_data["data"]["assets"]
        assert data["version"] == 2
        assert data["asset_count"] == 2

    def test_get_portfolio_versions(self, authorized_client, test_user, db_session):
        """Test getting portfolio version history"""
        portfolio = PortfolioFactory(user_id=test_user["id"])
        db_session.add(portfolio)
        db_session.flush()  # Ensure ID is generated
        db_session.commit()
        
        # Add some versions
        versions = [
            PortfolioVersionFactory(
                portfolio_id=portfolio.id,
                version=i+1
            ) for i in range(3)
        ]
        for version in versions:
            db_session.add(version)
        db_session.commit()

        response = authorized_client.get(
            f"{settings.API_V1_STR}/portfolios/{portfolio.id}/versions"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert data[0]["version"] == 3  # Latest version first
        assert data[1]["version"] == 2
        assert data[2]["version"] == 1

    @pytest.mark.parametrize("tier,expected_status", [
        (SubscriptionTier.FREE, status.HTTP_403_FORBIDDEN),
        (SubscriptionTier.PREMIUM, status.HTTP_200_OK)
    ])
    def test_sync_portfolio_subscription_check(
        self, authorized_client, test_user, db_session, tier, expected_status
    ):
        """Test portfolio sync with different subscription tiers"""
        # Update user's subscription tier
        user = db_session.query(User).filter(User.id == test_user["id"]).first()
        user.subscription_tier = tier
        db_session.commit()

        portfolio = PortfolioFactory(user_id=test_user["id"])
        db_session.add(portfolio)
        db_session.flush()  # Ensure ID is generated
        db_session.commit()

        sync_data = {
            "client_data": {
                "assets": {
                    "bitcoin": {
                        "amount": "1.0",
                        "cost_basis": "35000.00"
                    }
                },
                "settings": {"default_currency": "USD"},
                "metadata": {
                    "last_sync": datetime.now(timezone.utc).isoformat()
                },
                "schema_version": "1.0.0"
            },
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "client_version": 1,
            "force": False,
            "device_id": "test_device"
        }

        response = authorized_client.post(
            f"{settings.API_V1_STR}/portfolios/{portfolio.id}/sync",
            json=sync_data
        )
        assert response.status_code == expected_status

    def test_get_sync_status(self, authorized_client, test_user, db_session):
        """Test getting portfolio sync status"""
        portfolio = PortfolioFactory(
            user_id=test_user["id"],
            is_cloud_synced=True,
            last_sync_at=datetime.now(timezone.utc)
        )
        db_session.add(portfolio)
        db_session.flush()  # Ensure ID is generated
        db_session.commit()

        response = authorized_client.get(
            f"{settings.API_V1_STR}/portfolios/{portfolio.id}/sync/status"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "last_sync_at" in data
        assert data["is_synced"] is True
