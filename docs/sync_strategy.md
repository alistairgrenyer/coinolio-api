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
- Compare client and server timestamps
- Check version numbers
- Detect data structure differences using DeepDiff
- Consider device identifiers

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

## Conflict Resolution

### Priority Rules
1. Server data takes precedence in conflicts
2. Newer timestamps win in version conflicts
3. Device hierarchy can override timestamp rules

### Resolution Process
```python
if server_timestamp > client_timestamp:
    use_server_data()
elif client_timestamp > server_timestamp:
    use_client_data()
else:
    use_server_data()  # Server preference
```

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
1. Store last sync timestamp
2. Track local changes
3. Implement retry logic
4. Handle offline mode

### Server Implementation
1. Validate incoming data
2. Preserve sync metadata
3. Log sync operations
4. Monitor sync patterns

## Testing Strategy

### Key Test Scenarios
1. Clean sync (no conflicts)
2. Conflict resolution
3. Network failure recovery
4. Concurrent modifications
5. Large data sets

### Example Test Case
```python
def test_conflict_resolution():
    # Setup conflicting states
    server_data = create_portfolio_with_timestamp(t1)
    client_data = create_portfolio_with_timestamp(t2)
    
    # Attempt sync
    result = sync_manager.merge_portfolios(server_data, client_data)
    
    # Verify resolution
    assert result.version > max(server_data.version, client_data.version)
    assert result.last_sync_at > max(server_data.last_sync_at, 
                                   client_data.last_sync_at)
```

## Performance Considerations

### Optimization Strategies
1. Minimize data transfer
2. Efficient change detection
3. Batch synchronization
4. Background processing

### Monitoring
- Sync duration metrics
- Conflict rate tracking
- Error rate monitoring
- Data size tracking

## Future Improvements

### Planned Enhancements
1. Granular conflict resolution
2. Multi-device sync
3. Real-time synchronization
4. Differential sync
5. Compression for large datasets

### Migration Path
- Versioned sync protocol
- Backward compatibility
- Gradual feature rollout
- Client update strategy
