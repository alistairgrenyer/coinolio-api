from datetime import datetime, timezone
from typing import Any, Optional, Union

from deepdiff import DeepDiff
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.schemas.portfolio_sync import ChangeType, SyncChange, SyncRequest


class SyncManager:
    """
    Handles synchronization of portfolio data between mobile app and server.
    Uses a simple last-write-wins strategy with conflict detection.
    """
    
    def __init__(self):
        self.SYNC_VERSION = "1.0.0"

    def generate_sync_metadata(self, device_id: str) -> dict[str, Any]:
        """Generate sync metadata for a portfolio update"""
        return {
            "sync_version": self.SYNC_VERSION,
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _ensure_timezone_aware(self, dt: Optional[datetime]) -> datetime:
        """Ensure a datetime is timezone-aware, defaulting to UTC"""
        if dt is None:
            return datetime.fromtimestamp(0, tz=timezone.utc)
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return datetime.fromtimestamp(0, tz=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def get_sync_status(self, portfolio: Portfolio, sync_request: SyncRequest) -> dict[str, Any]:
        """Get sync status and detect conflicts"""
        if not portfolio.is_cloud_synced:
            return {
                "needs_sync": True,
                "has_conflicts": False,
                "server_version": portfolio.version,
                "server_last_sync": portfolio.last_sync_at
            }

        # Check for version mismatch
        if sync_request.client_version != portfolio.version:
            return {
                "needs_sync": True,
                "has_conflicts": True,
                "server_version": portfolio.version,
                "server_last_sync": portfolio.last_sync_at
            }

        # Check for data differences
        if sync_request.client_data != portfolio.data:
            # Ensure both timestamps are timezone-aware
            client_time = self._ensure_timezone_aware(sync_request.last_sync_at)  # noqa: F841
            server_time = self._ensure_timezone_aware(portfolio.last_sync_at)  # noqa: F841

            # Compare timestamps to determine sync direction
            return {
                "needs_sync": True,
                "has_conflicts": False,
                "server_version": portfolio.version,
                "server_last_sync": portfolio.last_sync_at
            }

        # No sync needed
        return {
            "needs_sync": False,
            "has_conflicts": False,
            "server_version": portfolio.version,
            "server_last_sync": portfolio.last_sync_at
        }

    def merge_portfolios(self, portfolio: Portfolio, sync_request: SyncRequest) -> dict[str, Any]:
        """
        Merge client data with server data using last-write-wins strategy.
        Returns the merged data.
        """
        # Compare timestamps
        client_time = self._ensure_timezone_aware(sync_request.last_sync_at)
        server_time = self._ensure_timezone_aware(portfolio.last_sync_at)

        # Use client data if it's newer, otherwise keep server data
        if client_time > server_time:
            merged_data = sync_request.client_data.copy()
        else:
            merged_data = portfolio.data.copy()

        # Update metadata
        if "metadata" not in merged_data:
            merged_data["metadata"] = {}
        merged_data["metadata"].update(self.generate_sync_metadata(sync_request.device_id))

        return merged_data

    def detect_changes(self, old_data: dict[str, Any], new_data: dict[str, Any]) -> list[SyncChange]:
        """
        Detect changes between old and new portfolio data.
        Returns a list of SyncChange objects.
        """
        changes = []
        diff = DeepDiff(old_data, new_data, ignore_order=True)
        
        # Print the diff for debugging
        print("\nDeepDiff Output:")
        print("Added:", diff.get("dictionary_item_added", []))
        print("Removed:", diff.get("dictionary_item_removed", []))
        print("Changed:", diff.get("values_changed", []))
        print("Type Changed:", diff.get("type_changes", []))

        # Handle added items
        for path in diff.get("dictionary_item_added", []):
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "").replace("'", "")
            value = self._get_value_by_path(new_data, clean_path)
            changes.append(SyncChange(
                type=ChangeType.ADDED,
                path=clean_path,
                value=value if isinstance(value, dict) else {"value": value}
            ))

        # Handle removed items
        for path in diff.get("dictionary_item_removed", []):
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "").replace("'", "")
            changes.append(SyncChange(
                type=ChangeType.DELETED,
                path=clean_path
            ))

        # Handle modified items
        for path in diff.get("values_changed", []):
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "").replace("'", "")
            value = self._get_value_by_path(new_data, clean_path)
            changes.append(SyncChange(
                type=ChangeType.MODIFIED,
                path=clean_path,
                value=value if isinstance(value, dict) else {"value": value}
            ))

        # Handle dictionary value changes
        for path in diff.get("type_changes", []):
            clean_path = path.replace("root['", "").replace("']['", ".").replace("']", "").replace("'", "")
            value = self._get_value_by_path(new_data, clean_path)
            changes.append(SyncChange(
                type=ChangeType.MODIFIED,
                path=clean_path,
                value=value if isinstance(value, dict) else {"value": value}
            ))
        
        # Print the changes for debugging
        print("\nDetected Changes:")
        for change in changes:
            print(f"Type: {change.type}, Path: {change.path}, Value: {change.value}")

        return changes

    def _get_value_by_path(self, data: dict[str, Any], path: str) -> Union[dict[str, Any], list[Any], str, int, float, bool, None]:
        """Get a value from a nested dictionary using a dot-separated path"""
        current = data
        for key in path.split('.'):
            if isinstance(current, dict):
                current = current.get(key, {})
            else:
                return current
        return current

    def merge_portfolios_db(
        self,
        portfolio: Portfolio,
        sync_request: SyncRequest,
        db: Session
    ) -> Portfolio:
        """
        Merge portfolios and update database.
        Returns the updated portfolio.
        """
        # Get sync status
        status = self.get_sync_status(portfolio, sync_request)
        
        if not status["needs_sync"]:
            return portfolio
        
        # Detect changes between client and server data
        changes = self.detect_changes(portfolio.data, sync_request.client_data)  # noqa: F841
        
        # Merge data
        merged_data = self.merge_portfolios(portfolio, sync_request)
        
        # Update portfolio
        portfolio.data = merged_data
        portfolio.version += 1
        portfolio.last_sync_at = datetime.now(timezone.utc)
        portfolio.last_sync_device = sync_request.device_id
        portfolio.is_cloud_synced = True
        
        # Save changes
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        
        return portfolio
