# Authentication Strategy

## Overview
This document outlines Coinolio's authentication strategy, including both registered users and guest access. The system is designed to provide a seamless experience for new users while maintaining security and rate limiting capabilities.

## Authentication Types

### 1. Registered Users (Current Implementation)
- Users register with email and password
- Authentication using JWT (JSON Web Tokens)
- Two-token system:
  - Access Token: Short-lived (minutes)
  - Refresh Token: Long-lived (days), stored in database
- Full access to features based on subscription tier
- User data stored in database

### 2. Guest Access (New Implementation)
- No database storage required
- Stateless authentication using JWT
- Token contains guest metadata:
  - Guest ID (UUID)
  - Creation timestamp
  - Rate limit tier
  - Request origin (IP hash)
- Limited to read-only operations
- Can be upgraded to full account by registering

## Token System

### Access Token Structure
1. Registered Users:
```json
{
    "sub": "user@example.com",
    "exp": 1234567890,
    "type": "registered",
    "tier": "free|premium",
    "jti": "unique_token_id"
}
```

2. Guest Users:
```json
{
    "sub": "guest:uuid4",
    "exp": 1234567890,
    "type": "guest",
    "created_at": 1234567890,
    "origin": "hashed_ip",
    "jti": "unique_token_id"
}
```

### Token Management
- Guest tokens expire after 1 hour
- No refresh tokens for guests
- Token blacklisting via Redis for revoked tokens
- Rate limiting based on combined factors:
  - Token JTI (unique token ID)
  - Guest ID
  - IP hash
  - User agent fingerprint

## User Tiers

1. Guest Users
   - Rate limits: 30 requests/minute
   - Historical data access: 7 days
   - Read-only access
   - No portfolio storage
   - Token expires in 1 hour
   - Must provide consistent user agent
   - IP binding for token validity

2. Free Registered Users
   - Rate limits: 60 requests/minute
   - Historical data access: 7 days
   - Full read access
   - One portfolio storage
   - Token expires in 1 hour
   - Refresh token valid for 7 days
   - Device tracking for suspicious activity

3. Premium Users
   - Rate limits: 120 requests/minute
   - Extended historical data (365 days)
   - Full read/write access
   - Multiple portfolios (up to 10)
   - Priority support
   - Concurrent device support
   - No IP binding restrictions

## Security Measures

### 1. Request Validation
- Token integrity check
- IP validation against token origin
- User agent consistency check
- Request timestamp validation
- Payload size limits
- Input validation and sanitization

### 2. Rate Limiting Strategy
```python
RATE_LIMITS = {
    'guest': {
        'requests_per_min': 30,
        'requests_per_hour': 1000,
        'concurrent_requests': 5,
        'max_payload_size': '50kb'
    },
    'free': {
        'requests_per_min': 60,
        'requests_per_hour': 1000,
        'concurrent_requests': 10,
        'max_payload_size': '50kb'
    },
    'premium': {
        'requests_per_min': 120,
        'concurrent_requests': 20,
        'max_payload_size': '100kb'
    }
}

ENDPOINT_LIMITS = {
    '/api/v1/historical': {
        'guest': {'max_requests_per_min': 10},
        'free': {'max_requests_per_min': 20}
    }
}
```

### 3. Abuse Prevention
1. Token Security
   - JTI (JWT ID) tracking for token uniqueness
   - IP binding for guest/free tokens
   - User agent fingerprinting
   - Token expiration and rotation

2. Request Pattern Monitoring
   - Concurrent request limiting
   - Request burst detection
   - Suspicious pattern detection
   - Geographic anomaly detection

3. Resource Usage Controls
   - Maximum payload size limits
   - Request complexity limits
   - Response size limits
   - Pagination enforcement

4. Automated Threat Response
   - Progressive rate limit reduction
   - Temporary IP blocking
   - Token revocation
   - User agent blacklisting

5. Data Access Controls
   - Historical data request throttling
   - Maximum symbols per request
   - Timeframe restrictions
   - Cache enforcement

### 4. Additional Security Measures
1. Request Validation
   - CORS restrictions
   - Content-Type enforcement
   - HTTP method validation
   - Required header checks

2. Error Handling
   - Generic error messages
   - Rate limit status endpoints
   - Graceful degradation
   - Error response throttling

3. Monitoring and Alerts
   - Abuse pattern detection
   - Rate limit threshold alerts
   - Geographic anomaly alerts
   - Token usage analytics

## Implementation Details

### Request Processing Pipeline
```python
1. Validate Request
   - Check token presence and format
   - Validate IP and user agent
   - Check payload size and format

2. Rate Limit Check
   - Check token-based limits
   - Check endpoint-specific limits
   - Check concurrent request limits

3. Resource Access
   - Validate access permissions
   - Check data access limits
   - Apply response size limits

4. Response
   - Apply rate limit headers
   - Include usage metrics
   - Cache control headers
```

### Security Headers
```http
X-RateLimit-Limit: [limit]
X-RateLimit-Remaining: [remaining]
X-RateLimit-Reset: [reset_time]
X-Request-ID: [request_uuid]
X-Token-Expires: [expiry_time]
```

## Migration Path
1. Start with guest token
2. Use read-only features
3. Register for full account
4. No data migration needed

## Future Enhancements
1. Security
   - Machine learning for abuse detection
   - Dynamic rate limiting
   - Reputation scoring
   - Device fingerprinting

2. Performance
   - Edge caching
   - Request coalescing
   - Response compression
   - Smart throttling

3. Monitoring
   - Usage analytics
   - Abuse patterns
   - Performance metrics
   - Conversion tracking
