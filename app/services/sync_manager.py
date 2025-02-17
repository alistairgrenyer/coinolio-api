from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import json
from deepdiff import DeepDiff

class SyncManager:
    def __init__(self):
        self.SYNC_VERSION = "1.0.0"

    def generate_sync_metadata(self, device_id: str) -> Dict[str, Any]:
        """Generate sync metadata for a portfolio update"""
        return {
            "sync_version": self.SYNC_VERSION,
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _merge_assets(
        self,
        base: Dict[str, Any],
        local: Dict[str, Any],
        remote: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Three-way merge of assets with conflict resolution:
        - If an asset is modified in both local and remote:
            - Use the most recent update based on transaction timestamps
            - If timestamps are equal, use remote (server) version
        - If an asset is added in one but not the other, keep it
        - If an asset is deleted in one but not the other:
            - If modified in the other, keep it
            - If not modified, delete it
        """
        merged = {}
        all_assets = set(base.keys()) | set(local.keys()) | set(remote.keys())

        for asset_id in all_assets:
            base_asset = base.get(asset_id)
            local_asset = local.get(asset_id)
            remote_asset = remote.get(asset_id)

            # Case 1: Asset exists in all versions
            if all(x is not None for x in [base_asset, local_asset, remote_asset]):
                # Check if modified in both local and remote
                if (DeepDiff(base_asset, local_asset) and 
                    DeepDiff(base_asset, remote_asset)):
                    # Use the most recently updated version
                    local_time = datetime.fromisoformat(local_asset.get("last_modified", "1970-01-01T00:00:00+00:00"))
                    remote_time = datetime.fromisoformat(remote_asset.get("last_modified", "1970-01-01T00:00:00+00:00"))
                    merged[asset_id] = local_asset if local_time > remote_time else remote_asset
                else:
                    # Use the modified version
                    if DeepDiff(base_asset, local_asset):
                        merged[asset_id] = local_asset
                    else:
                        merged[asset_id] = remote_asset

            # Case 2: Asset added in one version
            elif base_asset is None:
                # New asset - take whichever version exists
                merged[asset_id] = local_asset or remote_asset

            # Case 3: Asset deleted in one version
            else:
                # Keep if modified in the other version
                if local_asset and DeepDiff(base_asset, local_asset):
                    merged[asset_id] = local_asset
                elif remote_asset and DeepDiff(base_asset, remote_asset):
                    merged[asset_id] = remote_asset
                # Otherwise, consider it deleted

        return merged

    def merge_portfolios(
        self,
        base: Dict[str, Any],
        local: Dict[str, Any],
        remote: Dict[str, Any],
        device_id: str
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Perform three-way merge of portfolio data
        Returns (merged_data, had_conflicts)
        """
        had_conflicts = False
        merged = {
            "assets": self._merge_assets(
                base.get("assets", {}),
                local.get("assets", {}),
                remote.get("assets", {})
            ),
            "settings": local.get("settings", {}),  # Use local settings
            "metadata": self.generate_sync_metadata(device_id),
            "schema_version": self.SYNC_VERSION
        }

        # Check for conflicts
        if DeepDiff(
            base.get("assets", {}),
            local.get("assets", {})
        ) and DeepDiff(
            base.get("assets", {}),
            remote.get("assets", {})
        ):
            had_conflicts = True

        return merged, had_conflicts

    def detect_changes(
        self,
        base: Dict[str, Any],
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect changes between base and current versions
        Returns a summary of changes
        """
        diff = DeepDiff(base, current, ignore_order=True)
        
        changes = {
            "added_assets": [],
            "removed_assets": [],
            "modified_assets": [],
            "settings_changed": False
        }

        # Check for added/removed assets
        if "dictionary_item_added" in diff:
            added = [k for k in diff["dictionary_item_added"] if k.startswith("root['assets']")]
            changes["added_assets"] = [k.split("']['")[1][:-1] for k in added]

        if "dictionary_item_removed" in diff:
            removed = [k for k in diff["dictionary_item_removed"] if k.startswith("root['assets']")]
            changes["removed_assets"] = [k.split("']['")[1][:-1] for k in removed]

        # Check for modified assets
        if "values_changed" in diff:
            modified = [k for k in diff["values_changed"] if k.startswith("root['assets']")]
            changes["modified_assets"] = list(set(
                k.split("']['")[1] for k in modified
            ))

        # Check if settings were changed
        if any(k.startswith("root['settings']") for k in diff.get("values_changed", {})):
            changes["settings_changed"] = True

        return changes
