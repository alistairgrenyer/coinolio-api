import pytest
from copy import deepcopy
from datetime import datetime, timezone
from app.services.sync_manager import SyncManager
from app.models.portfolio import Portfolio
from app.schemas.portfolio_sync import SyncRequest, ChangeType

@pytest.fixture
def sync_manager():
    return SyncManager()

@pytest.fixture
def base_portfolio():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return Portfolio(
        id=1,
        user_id=1,
        name="Test Portfolio",
        data={
            "@portfolios": {
                "default": {
                    "assets": {
                        "btc": {
                            "amount": "1.0",
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
        },
        version=1,
        is_cloud_synced=True,
        last_sync_at=now,
        last_sync_device="test-device"
    )

@pytest.fixture
def sync_request(base_portfolio):
    now = datetime(2025, 1, 2, tzinfo=timezone.utc)
    return SyncRequest(
        client_data=base_portfolio.data,
        last_sync_at=now,
        client_version=1,
        device_id="test-device"
    )

def test_get_sync_status_no_conflicts(sync_manager, base_portfolio, sync_request):
    """Test sync status with no conflicts"""
    status = sync_manager.get_sync_status(base_portfolio, sync_request)
    assert status["needs_sync"] is False
    assert status["has_conflicts"] is False
    assert status["server_version"] == base_portfolio.version

def test_get_sync_status_version_mismatch(sync_manager, base_portfolio, sync_request):
    """Test sync status with version mismatch"""
    sync_request.client_version = 2
    status = sync_manager.get_sync_status(base_portfolio, sync_request)
    assert status["needs_sync"] is True
    assert status["has_conflicts"] is True
    assert status["server_version"] == base_portfolio.version

def test_get_sync_status_data_conflict(sync_manager, base_portfolio, sync_request):
    """Test sync status with data conflict"""
    # Modify client data
    client_data = deepcopy(sync_request.client_data)
    client_data["@portfolios"]["default"]["assets"]["btc"]["amount"] = "2.0"
    sync_request.client_data = client_data
    
    status = sync_manager.get_sync_status(base_portfolio, sync_request)
    assert status["needs_sync"] is True
    assert status["has_conflicts"] is False
    assert status["server_version"] == base_portfolio.version

def test_merge_portfolios(sync_manager, base_portfolio, sync_request):
    """Test merging portfolios with client data"""
    # Modify client data
    client_data = sync_request.client_data.copy()
    client_data["@portfolios"]["default"]["assets"]["btc"]["amount"] = "2.0"
    sync_request.client_data = client_data
    
    merged_data = sync_manager.merge_portfolios(base_portfolio, sync_request)
    assert merged_data["@portfolios"]["default"]["assets"]["btc"]["amount"] == "2.0"
    assert "metadata" in merged_data
    assert merged_data["metadata"]["device_id"] == sync_request.device_id

def test_detect_changes(sync_manager, base_portfolio, sync_request):
    """Test detecting changes between server and client data"""
    # Modify client data with multiple changes
    client_data = deepcopy(sync_request.client_data)
    
    # Add ETH asset
    client_data["@portfolios"]["default"]["assets"]["eth"] = {
        "amount": "10.0",
        "lastModified": datetime.now(timezone.utc).isoformat()
    }
    
    # Modify BTC amount
    client_data["@portfolios"]["default"]["assets"]["btc"]["amount"] = "2.0"
    
    changes = sync_manager.detect_changes(base_portfolio.data, client_data)
    
    # Print debug info
    print("\nTest Debug Info:")
    print("Original BTC Amount:", base_portfolio.data["@portfolios"]["default"]["assets"]["btc"]["amount"])
    print("Modified BTC Amount:", client_data["@portfolios"]["default"]["assets"]["btc"]["amount"])
    print("Changes:", changes)
    
    # Verify changes
    assert len(changes) == 2
    
    # Find the modified BTC change
    btc_change = next(
        (c for c in changes if c.path == "@portfolios.default.assets.btc.amount"),
        None
    )
    assert btc_change is not None, "BTC amount change not found"
    assert btc_change.type == ChangeType.MODIFIED
    assert btc_change.value["value"] == "2.0"
    
    # Find the added ETH change
    eth_change = next(
        (c for c in changes if c.path == "@portfolios.default.assets.eth"),
        None
    )
    assert eth_change is not None, "ETH asset addition not found"
    assert eth_change.type == ChangeType.ADDED
    assert eth_change.value["amount"] == "10.0"

def test_sync_status_timezone_handling(sync_manager, base_portfolio):
    """Test timezone handling in sync status"""
    # Create request with naive datetime
    naive_time = datetime(2025, 1, 2)
    client_data = deepcopy(base_portfolio.data)
    client_data["@portfolios"]["default"]["assets"]["btc"]["amount"] = "2.0"
    sync_request = SyncRequest(
        client_data=client_data,
        last_sync_at=naive_time,
        client_version=1,
        device_id="test-device"
    )
    
    status = sync_manager.get_sync_status(base_portfolio, sync_request)
    assert status["needs_sync"] is True
    assert status["has_conflicts"] is False
    assert status["server_version"] == base_portfolio.version
