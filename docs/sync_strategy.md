# Synchronization Strategy Documentation

## Overview
This document details the portfolio synchronization strategy implemented in Coinolio API, focusing on mobile-to-server data synchronization, conflict resolution, and data consistency.

## Sync Architecture

### Core Components
- `SyncManager`: Handles sync operations and conflict resolution
- `Portfolio Model`: Stores sync metadata and portfolio data
- `AsyncStorage Data`: Mobile app's source of truth

### Sync Metadata
- `version`: Incremental counter for change tracking
- `last_sync_at`: Timezone-aware timestamp of last sync
- `last_sync_device`: Device identifier for sync origin
- `is_cloud_synced`: Flag indicating sync status

## Synchronization Process

### 1. Sync Status Check
```python
# Client requests sync status
GET /api/v1/portfolios/{id}/sync-status
{
    "needs_sync": boolean,
    "has_conflicts": boolean,
    "server_version": int,
    "server_last_sync": datetime
}
```

### 2. Change Detection
The system uses DeepDiff to detect changes in nested portfolio data structures:

```python
# Example change detection
changes = sync_manager.detect_changes(server_data, client_data)

# Sample changes output
[
    SyncChange(
        type=ChangeType.MODIFIED,
        path="@portfolios.default.assets.btc.amount",
        value={"value": "2.0"}
    ),
    SyncChange(
        type=ChangeType.ADDED,
        path="@portfolios.default.assets.eth",
        value={
            "amount": "10.0",
            "lastModified": "2025-02-19T00:00:00Z"
        }
    )
]
```

Change types include:
- `ADDED`: New data added
- `DELETED`: Existing data removed
- `MODIFIED`: Data value changed

### 3. Merge Strategy
The system implements a "last-write-wins with server preference" strategy:

1. **No Conflict Case**:
   - Client ahead: Accept client changes
   - Server ahead: Client pulls server changes
   - Same version: No action needed

2. **Conflict Case**:
   - Compare timestamps (UTC)
   - Server data preferred in ambiguous cases
   - Increment version number
   - Update sync metadata

## Timezone Handling

### UTC Standardization
All datetime values are converted to UTC for consistent comparison:

```python
def ensure_timezone_aware(dt: Optional[datetime]) -> datetime:
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
```

### Datetime Comparison
- All timestamps are normalized to UTC
- Naive datetimes are assumed to be UTC
- ISO 8601 format used for string representation
- 'Z' suffix handled for UTC timestamps

## Error Handling

### Common Scenarios
1. **Network Failures**:
   - Retry mechanism
   - Local state preservation
   - Sync status tracking

2. **Data Corruption**:
   - Validation checks
   - Rollback capability
   - Error reporting

3. **Version Conflicts**:
   - Conflict detection
   - Resolution strategy
   - User notification

## Best Practices

### Client Implementation
1. Store last sync timestamp (UTC)
2. Track local changes
3. Implement retry logic
4. Handle offline mode
5. Validate timezone data

### Server Implementation
1. Validate incoming data
2. Preserve sync metadata
3. Log sync operations
4. Monitor sync patterns
5. Ensure UTC consistency

## Testing Strategy

### Unit Tests
1. **Change Detection**:
   ```python
   def test_detect_changes():
       """Test detecting changes between server and client data"""
       # Modify client data
       client_data["@portfolios"]["default"]["assets"]["btc"]["amount"] = "2.0"
       
       changes = sync_manager.detect_changes(server_data, client_data)
       assert len(changes) > 0
       assert changes[0].type == ChangeType.MODIFIED
   ```

2. **Timezone Handling**:
   ```python
   def test_timezone_handling():
       """Test timezone-aware datetime processing"""
       naive_time = datetime(2025, 1, 1)
       aware_time = ensure_timezone_aware(naive_time)
       assert aware_time.tzinfo == timezone.utc
   ```

3. **Conflict Resolution**:
   ```python
   def test_conflict_resolution():
       """Test merge strategy with conflicts"""
       status = sync_manager.get_sync_status(portfolio, sync_request)
       assert status["has_conflicts"] is False
       assert status["needs_sync"] is True
   ```

### Integration Tests
1. Full sync cycle validation
2. Network failure recovery
3. Concurrent sync handling
4. Performance monitoring

## Performance Considerations

### Optimization Techniques
1. Efficient change detection
2. Minimal data transfer
3. Batch processing
4. Caching strategies

### Monitoring Metrics
1. Sync duration
2. Conflict frequency
3. Data transfer size
4. Error rates

## Security Considerations

1. **Data Protection**:
   - Encrypted transmission
   - Secure storage
   - Access control

2. **Validation**:
   - Input sanitization
   - Schema validation
   - Type checking

3. **Audit Trail**:
   - Sync logging
   - Version history
   - Change tracking

## Future Improvements

1. **Q2 2025**:
   - Differential sync
   - Compression
   - Batch operations

2. **Q3 2025**:
   - Real-time sync
   - Conflict resolution UI
   - Sync analytics

3. **Q4 2025**:
   - Multi-device sync
   - Offline-first approach
   - Advanced conflict resolution
