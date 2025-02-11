import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from datetime import datetime

from app.models.user import User, Portfolio
from app.models.enums import SubscriptionTier

def test_create_portfolio_unauthorized(client: TestClient):
    """Test creating portfolio without authentication"""
    response = client.post("/api/v1/portfolios", json={
        "name": "Test Portfolio",
        "description": "Test description",
        "data": {}
    })
    assert response.status_code == 401

def test_create_portfolio_success(
    client: TestClient,
    normal_user_token: str,
    sample_portfolio_data: dict,
    mock_db: MagicMock,
    normal_user: User
):
    """Test successful portfolio creation"""
    # Mock the database query for get_current_user
    mock_db.query.return_value.filter.return_value.first.return_value = normal_user
    
    # Create a new portfolio instance for the response
    new_portfolio = Portfolio(
        id=1,
        name="Test Portfolio",
        description="Test description",
        user_id=normal_user.id,
        data=sample_portfolio_data,
        version=1,
        total_value_usd=0,
        asset_count=2,
        is_cloud_synced=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    new_portfolio.user = normal_user
    
    # Mock portfolio creation
    def refresh_side_effect(obj):
        obj.id = 1  # Simulate database assigning an ID
    
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = refresh_side_effect
    
    response = client.post(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {normal_user_token}"},
        json={
            "name": "Test Portfolio",
            "description": "Test description",
            "data": sample_portfolio_data
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Portfolio"
    assert data["description"] == "Test description"
    assert data["version"] == 1
    assert data["asset_count"] == 2
    assert "bitcoin" in data["data"]["assets"]
    assert "ethereum" in data["data"]["assets"]

def test_get_portfolios(
    client: TestClient,
    normal_user_token: str,
    test_portfolio: Portfolio,
    mock_db: MagicMock,
    normal_user: User
):
    """Test getting user's portfolios"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.return_value = normal_user
    mock_db.query.return_value.filter.return_value.all.return_value = [test_portfolio]
    
    response = client.get(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_portfolio.id
    assert data[0]["name"] == test_portfolio.name
    assert data[0]["description"] == test_portfolio.description
    assert data[0]["version"] == test_portfolio.version
    assert data[0]["total_value_usd"] == test_portfolio.total_value_usd
    assert data[0]["asset_count"] == test_portfolio.asset_count
    assert data[0]["is_cloud_synced"] == test_portfolio.is_cloud_synced

def test_get_portfolios_with_versions(
    client: TestClient,
    normal_user_token: str,
    test_portfolio: Portfolio,
    portfolio_version,
    mock_db: MagicMock,
    normal_user: User
):
    """Test getting portfolios with version history"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.return_value = normal_user
    mock_db.query.return_value.filter.return_value.all.return_value = [test_portfolio]
    
    response = client.get(
        "/api/v1/portfolios?include_versions=true",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    portfolio_data = data[0]
    assert portfolio_data["id"] == test_portfolio.id
    assert portfolio_data["name"] == test_portfolio.name
    assert len(portfolio_data["versions"]) == 1
    version_data = portfolio_data["versions"][0]
    assert version_data["version"] == portfolio_version.version
    assert version_data["total_value_usd"] == portfolio_version.total_value_usd
    assert version_data["asset_count"] == portfolio_version.asset_count

def test_get_portfolio_not_found(
    client: TestClient,
    normal_user_token: str,
    mock_db: MagicMock,
    normal_user: User
):
    """Test getting non-existent portfolio"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [normal_user, None]
    
    response = client.get(
        "/api/v1/portfolios/999",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    assert response.status_code == 404

def test_get_portfolio_unauthorized_access(
    client: TestClient,
    normal_user_token: str,
    premium_portfolio: Portfolio,
    mock_db: MagicMock,
    normal_user: User
):
    """Test accessing another user's portfolio"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [normal_user, None]
    
    response = client.get(
        f"/api/v1/portfolios/{premium_portfolio.id}",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    assert response.status_code == 404

def test_update_portfolio(
    client: TestClient,
    normal_user_token: str,
    test_portfolio: Portfolio,
    sample_portfolio_data: dict,
    mock_db: MagicMock,
    normal_user: User
):
    """Test updating portfolio"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [normal_user, test_portfolio]
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # Modify the sample data
    updated_data = sample_portfolio_data.copy()
    updated_data["assets"]["bitcoin"]["amount"] = "2.0"
    
    response = client.put(
        f"/api/v1/portfolios/{test_portfolio.id}",
        headers={"Authorization": f"Bearer {normal_user_token}"},
        json={
            "name": "Updated Portfolio",
            "data": updated_data
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Portfolio"
    assert data["version"] == 2
    assert data["data"]["assets"]["bitcoin"]["amount"] == "2.0"

def test_sync_portfolio_unauthorized(
    client: TestClient,
    normal_user_token: str,
    test_portfolio: Portfolio,
    mock_db: MagicMock,
    normal_user: User
):
    """Test syncing portfolio without premium subscription"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [normal_user, test_portfolio]
    
    response = client.post(
        f"/api/v1/portfolios/{test_portfolio.id}/sync",
        headers={"Authorization": f"Bearer {normal_user_token}"},
        json={
            "device_id": "test_device",
            "local_data": test_portfolio.data,
            "base_version": 1
        }
    )
    assert response.status_code == 403

def test_sync_portfolio_success(
    client: TestClient,
    premium_user_token: str,
    premium_portfolio: Portfolio,
    portfolio_version,
    mock_db: MagicMock,
    premium_user: User
):
    """Test successful portfolio sync"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [premium_user, premium_portfolio]
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # Modify some data for sync
    local_data = premium_portfolio.data.copy()
    local_data["assets"]["bitcoin"]["amount"] = "3.0"
    
    response = client.post(
        f"/api/v1/portfolios/{premium_portfolio.id}/sync",
        headers={"Authorization": f"Bearer {premium_user_token}"},
        json={
            "device_id": "test_device",
            "local_data": local_data,
            "base_version": 1,
            "force": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 2
    assert data["data"]["assets"]["bitcoin"]["amount"] == "3.0"
    assert data["sync_metadata"]["had_conflicts"] is False

def test_sync_portfolio_conflict(
    client: TestClient,
    premium_user_token: str,
    premium_portfolio: Portfolio,
    portfolio_version,
    mock_db: MagicMock,
    premium_user: User
):
    """Test portfolio sync with conflicts"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [premium_user, premium_portfolio]
    
    # Create conflicting changes
    local_data = premium_portfolio.data.copy()
    local_data["assets"]["bitcoin"]["amount"] = "3.0"
    
    response = client.post(
        f"/api/v1/portfolios/{premium_portfolio.id}/sync",
        headers={"Authorization": f"Bearer {premium_user_token}"},
        json={
            "device_id": "test_device",
            "local_data": local_data,
            "base_version": 1,
            "force": False
        }
    )
    
    assert response.status_code == 409
    assert "Conflicts detected" in response.json()["detail"]

def test_get_portfolio_versions(
    client: TestClient,
    normal_user_token: str,
    test_portfolio: Portfolio,
    portfolio_version,
    mock_db: MagicMock,
    normal_user: User
):
    """Test getting portfolio version history"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [normal_user, test_portfolio]
    test_portfolio.versions = [portfolio_version]
    
    response = client.get(
        f"/api/v1/portfolios/{test_portfolio.id}/versions",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["version"] == 1
    assert "change_summary" in data[0]

def test_get_sync_status(
    client: TestClient,
    premium_user_token: str,
    premium_portfolio: Portfolio,
    portfolio_version,
    mock_db: MagicMock,
    premium_user: User
):
    """Test getting portfolio sync status"""
    # Mock the database queries
    mock_db.query.return_value.filter.return_value.first.side_effect = [premium_user, premium_portfolio]
    premium_portfolio.versions = [portfolio_version]
    
    response = client.get(
        f"/api/v1/portfolios/{premium_portfolio.id}/sync/status",
        headers={"Authorization": f"Bearer {premium_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_synced"] is True
    assert data["current_version"] == 1
    assert "last_sync" in data
