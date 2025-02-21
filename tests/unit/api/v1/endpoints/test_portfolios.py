from datetime import datetime, timezone
from copy import deepcopy
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.enums import SubscriptionTier

settings = get_settings()

def normalize_datetime(value):
    """Normalize datetime strings to a consistent format"""
    if isinstance(value, str):
        try:
            # Handle 'Z' suffix and other ISO formats
            if value.endswith('Z'):
                value = value.replace('Z', '+00:00')
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            # Return only the date part for comparison
            return dt.astimezone(timezone.utc).date().isoformat()
        except ValueError:
            return value
    elif isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        # Return only the date part for comparison
        return value.astimezone(timezone.utc).date().isoformat()
    return value

def compare_data(d1, d2):
    """Compare data structures with datetime normalization"""
    if isinstance(d1, dict) and isinstance(d2, dict):
        # Skip metadata comparison since it contains timestamps
        if "metadata" in d1 and "metadata" in d2:
            d1 = {k: v for k, v in d1.items() if k != "metadata"}
            d2 = {k: v for k, v in d2.items() if k != "metadata"}
        
        assert set(d1.keys()) == set(d2.keys()), f"Keys don't match: {d1.keys()} != {d2.keys()}"
        for key in d1:
            compare_data(d1[key], d2[key])
    elif isinstance(d1, list) and isinstance(d2, list):
        assert len(d1) == len(d2), f"List lengths don't match: {len(d1)} != {len(d2)}"
        for i1, i2 in zip(sorted(d1), sorted(d2)):
            compare_data(i1, i2)
    else:
        n1, n2 = normalize_datetime(d1), normalize_datetime(d2)
        assert n1 == n2, f"Values don't match after normalization: {n1} != {n2}"

def create_portfolio_data() -> dict:
    """Create test portfolio data"""
    now = datetime.now(timezone.utc)
    return {
        "name": "Test Portfolio",
        "data": {
            "@portfolios": {
                "default": {
                    "assets": {
                        "btc": {
                            "amount": "1.5",
                            "lastModified": now.isoformat()
                        }
                    },
                    "settings": {
                        "currency": "USD"
                    }
                }
            },
            "metadata": {
                "sync_version": "1.0.0",
                "device_id": "test-device",
                "timestamp": now.isoformat()
            }
        }
    }

@pytest.fixture
def test_portfolio(db_session: Session, test_user: User) -> Portfolio:
    """Create a test portfolio"""
    portfolio_data = create_portfolio_data()
    portfolio = Portfolio(
        name=portfolio_data["name"],
        data=portfolio_data["data"],
        user_id=test_user.id,
        version=1,
        is_cloud_synced=True,
        last_sync_at=datetime.now(timezone.utc),
        last_sync_device="test-device"
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio

class TestPortfolioEndpoints:
    def test_create_portfolio_success(self, authorized_client, test_user):
        """Test successful portfolio creation"""
        portfolio_data = create_portfolio_data()
        response = authorized_client.post("/api/v1/portfolios/", json=portfolio_data)
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["name"] == portfolio_data["name"]
        compare_data(response_json["data"], portfolio_data["data"])

    def test_get_portfolios(self, authorized_client, test_portfolio):
        """Test getting all portfolios"""
        response = authorized_client.get("/api/v1/portfolios/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == test_portfolio.id

    def test_get_portfolio(self, authorized_client, test_portfolio):
        """Test getting a specific portfolio"""
        response = authorized_client.get(f"/api/v1/portfolios/{test_portfolio.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == test_portfolio.id

    def test_update_portfolio(self, authorized_client, test_portfolio):
        """Test updating a portfolio"""
        update_data = {
            "name": "Updated Portfolio",
            "data": test_portfolio.data
        }
        response = authorized_client.put(
            f"/api/v1/portfolios/{test_portfolio.id}",
            json=update_data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == update_data["name"]

    def test_sync_portfolio_premium_only(self, authorized_client, test_portfolio):
        """Test sync endpoint requires premium subscription"""
        sync_data = {
            "client_data": test_portfolio.data,
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "client_version": 1,
            "device_id": "test-device"
        }
        response = authorized_client.post(
            f"/api/v1/portfolios/{test_portfolio.id}/sync",
            json=sync_data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sync_portfolio_success(self, authorized_client, test_portfolio, test_user, db_session):
        """Test successful portfolio sync"""
        # Update user to premium
        test_user.subscription_tier = SubscriptionTier.PREMIUM
        db_session.add(test_user)
        db_session.commit()
        
        # Store initial version and data
        initial_version = test_portfolio.version
        initial_data = deepcopy(test_portfolio.data)
        
        # Create sync data with timezone-aware datetime and modified data
        modified_data = deepcopy(test_portfolio.data)
        modified_data["@portfolios"]["default"]["assets"]["btc"]["amount"] = "2.0"
        modified_data["metadata"]["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        sync_data = {
            "client_data": modified_data,
            "last_sync_at": datetime.now(timezone.utc).isoformat(),
            "client_version": initial_version,
            "device_id": "test-device"
        }
        
        # Print debug info before sync
        print("\nDebug Info Before Sync:")
        print(f"Initial Portfolio Version: {initial_version}")
        print(f"Initial BTC Amount: {initial_data['@portfolios']['default']['assets']['btc']['amount']}")
        print(f"Modified BTC Amount: {modified_data['@portfolios']['default']['assets']['btc']['amount']}")
        
        response = authorized_client.post(
            f"/api/v1/portfolios/{test_portfolio.id}/sync",
            json=sync_data
        )
        
        assert response.status_code == status.HTTP_200_OK, f"Unexpected status code: {response.status_code}"
        result = response.json()
        
        # Print debug info after sync
        print("\nDebug Info After Sync:")
        print(f"Response Success: {result['success']}")
        print(f"Response Version: {result['version']}")
        print(f"Response Changes: {result.get('changes', [])}")
        print(f"Response BTC Amount: {result['data']['@portfolios']['default']['assets']['btc']['amount']}")
        
        # Basic assertions
        assert result["success"] is True, "Sync was not successful"
        assert result["version"] > initial_version, f"Expected version > {initial_version}, got {result['version']}"
        assert result["data"] is not None, "Response data is None"
        assert isinstance(result["changes"], list), "Changes is not a list"
        
        # Verify changes list
        assert len(result["changes"]) > 0, (
            f"Expected changes in sync response. Initial amount: {initial_data['@portfolios']['default']['assets']['btc']['amount']}, "
            f"Modified amount: {modified_data['@portfolios']['default']['assets']['btc']['amount']}"
        )
        
        # Verify the data was actually changed in database
        db_session.refresh(test_portfolio)
        assert test_portfolio.version > initial_version, (
            f"Portfolio version not incremented. Initial: {initial_version}, Current: {test_portfolio.version}"
        )
        assert test_portfolio.data["@portfolios"]["default"]["assets"]["btc"]["amount"] == "2.0", (
            f"Portfolio BTC amount not updated. Got: {test_portfolio.data['@portfolios']['default']['assets']['btc']['amount']}"
        )
        
        # Compare data with normalization
        compare_data(result["data"], sync_data["client_data"])

    def test_get_sync_status(self, authorized_client, test_portfolio, test_user):
        """Test getting sync status"""
        # Update user to premium
        test_user.subscription_tier = SubscriptionTier.PREMIUM
        
        response = authorized_client.get(
            f"/api/v1/portfolios/{test_portfolio.id}/sync/status",
            params={
                "client_version": test_portfolio.version,
                "device_id": "test-device"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "needs_sync" in result
        assert "has_conflicts" in result
        assert "server_version" in result
        assert "server_last_sync" in result
