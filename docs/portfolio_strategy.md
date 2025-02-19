# Portfolio Strategy Documentation

## Overview
This document outlines the portfolio management strategy implemented in Coinolio API, focusing on data structure, storage, and validation approaches.

## Data Model

### Core Structure
- Portfolios are stored as flexible JSON documents using `JSONEncodedDict`
- Raw mobile app AsyncStorage data is preserved to maintain client-side compatibility
- Metadata fields track synchronization state and version history

### Key Fields
- `id`: Unique identifier for the portfolio
- `user_id`: Owner of the portfolio
- `data`: JSON-encoded portfolio data from mobile AsyncStorage
- `version`: Incremental version number for sync tracking
- `last_sync_at`: Timezone-aware timestamp of last sync
- `last_sync_device`: Identifier of last syncing device

## Data Storage Strategy

### JSON Storage
- Uses PostgreSQL's JSONB type for efficient storage and querying
- Maintains flexibility for future schema changes
- Preserves client-side data structure

### Validation
- Pydantic models ensure data integrity
- Basic schema validation on portfolio creation/update
- Flexible schema allows for client-side innovations

## Portfolio Management

### Creation
1. Initialize with empty or provided AsyncStorage data
2. Set initial version to 1
3. Record creation timestamp with timezone
4. Generate unique portfolio ID

### Updates
1. Validate incoming data structure
2. Preserve existing metadata
3. Increment version number
4. Update sync timestamp
5. Record updating device ID

## Security Considerations

### Data Access
- Portfolio access restricted to owning user
- Read/write permissions enforced at API level
- Sensitive data should be encrypted client-side

### Data Integrity
- Version tracking prevents unauthorized modifications
- Timestamps ensure accurate sync state
- Device IDs help track data lineage

## Best Practices

### Portfolio Creation
```python
# Example portfolio creation
portfolio = Portfolio(
    user_id=user.id,
    data={},  # Empty initial state
    version=1,
    last_sync_at=datetime.now(timezone.utc),
    last_sync_device="initial"
)
```

### Data Updates
```python
# Example portfolio update
portfolio.data = new_data
portfolio.version += 1
portfolio.last_sync_at = datetime.now(timezone.utc)
portfolio.last_sync_device = device_id
```

## Future Considerations

### Planned Improvements
- Enhanced data validation rules
- Portfolio archiving mechanism
- Data compression for large portfolios
- Historical state tracking

### Migration Strategy
- Support for schema evolution
- Backward compatibility guarantees
- Migration tools for legacy data
