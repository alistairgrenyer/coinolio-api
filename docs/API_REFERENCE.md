# Coinolio API Reference

## Authentication Endpoints

### Register User
- **Endpoint**: `POST /api/v1/auth/register`
- **Description**: Register a new user
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "is_active": true,
    "created_at": "2025-02-17T23:47:47Z",
    "role": "USER",
    "subscription_tier": "FREE",
    "subscription_expires_at": null,
    "stripe_customer_id": null,
    "stripe_subscription_id": null,
    "portfolios": []
  }
  ```

### Login
- **Endpoint**: `POST /api/v1/auth/token`
- **Description**: Login to get access token
- **Request Body**:
  ```json
  {
    "username": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
    "refresh_token": "a8b7c6d5-e4f3-g2h1-i0j9-k8l7m6n5o4p3",
    "token_type": "bearer"
  }
  ```

### Refresh Token
- **Endpoint**: `POST /api/v1/auth/refresh`
- **Description**: Get new access token using refresh token
- **Request Body**:
  ```json
  {
    "refresh_token": "a8b7c6d5-e4f3-g2h1-i0j9-k8l7m6n5o4p3"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1...",
    "refresh_token": "p3o4n5m6l7k8-j9i0h1g2-f3e4d5c6b7a8",
    "token_type": "bearer"
  }
  ```

### Get Current User
- **Endpoint**: `GET /api/v1/auth/me`
- **Description**: Get current user information
- **Response**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "is_active": true,
    "created_at": "2025-02-17T23:47:47Z",
    "role": "USER",
    "subscription_tier": "FREE",
    "subscription_expires_at": null,
    "stripe_customer_id": null,
    "stripe_subscription_id": null,
    "portfolios": []
  }
  ```

## Portfolio Endpoints

### Create Portfolio
- **Endpoint**: `POST /api/v1/portfolios/`
- **Description**: Create a new portfolio
- **Request Body**:
  ```json
  {
    "name": "My Portfolio",
    "description": "My crypto investments",
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
        "price_alerts": true
      },
      "metadata": {
        "created_from": "web",
        "last_modified": "2025-02-17T23:47:47Z"
      },
      "schema_version": "1.0.0"
    }
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "name": "My Portfolio",
    "description": "My crypto investments",
    "is_cloud_synced": false,
    "created_at": "2025-02-17T23:47:47Z",
    "updated_at": "2025-02-17T23:47:47Z",
    "version": 1,
    "data": { ... },
    "total_value_usd": 52500.0,
    "asset_count": 1,
    "last_sync_at": null,
    "versions": []
  }
  ```

### Get All Portfolios
- **Endpoint**: `GET /api/v1/portfolios/`
- **Description**: Get all portfolios for the current user
- **Query Parameters**:
  - `include_versions` (boolean): Include version history
  - `limit_versions` (integer): Number of versions to include
- **Response**:
  ```json
  [
    {
      "id": 1,
      "name": "My Portfolio",
      "description": "My crypto investments",
      "is_cloud_synced": false,
      "created_at": "2025-02-17T23:47:47Z",
      "updated_at": "2025-02-17T23:47:47Z",
      "version": 1,
      "data": { ... },
      "total_value_usd": 52500.0,
      "asset_count": 1,
      "last_sync_at": null,
      "versions": []
    }
  ]
  ```

### Get Portfolio
- **Endpoint**: `GET /api/v1/portfolios/{portfolio_id}`
- **Description**: Get a specific portfolio
- **Query Parameters**:
  - `include_versions` (boolean): Include version history
  - `limit_versions` (integer): Number of versions to include
- **Response**: Same as single portfolio in Get All Portfolios

### Update Portfolio
- **Endpoint**: `PUT /api/v1/portfolios/{portfolio_id}`
- **Description**: Update a portfolio
- **Request Body**:
  ```json
  {
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
      "settings": {
        "default_currency": "USD"
      },
      "metadata": {
        "last_modified": "2025-02-17T23:47:47Z"
      },
      "schema_version": "1.0.0"
    }
  }
  ```
- **Response**: Same as Create Portfolio response

### Get Portfolio Versions
- **Endpoint**: `GET /api/v1/portfolios/{portfolio_id}/versions`
- **Description**: Get version history for a portfolio
- **Query Parameters**:
  - `limit` (integer): Number of versions to return
  - `offset` (integer): Offset for pagination
- **Response**:
  ```json
  [
    {
      "version": 2,
      "data": { ... },
      "created_at": "2025-02-17T23:47:47Z",
      "total_value_usd": 105000.0,
      "asset_count": 2,
      "change_summary": {
        "added_assets": ["ethereum"],
        "removed_assets": [],
        "modified_assets": ["bitcoin"]
      }
    }
  ]
  ```

### Sync Portfolio (Premium Feature)
- **Endpoint**: `POST /api/v1/portfolios/{portfolio_id}/sync`
- **Description**: Sync portfolio with cloud storage
- **Request Body**:
  ```json
  {
    "client_data": {
      "assets": {
        "bitcoin": {
          "amount": "1.0",
          "cost_basis": "35000.00"
        }
      },
      "settings": {
        "default_currency": "USD"
      },
      "metadata": {
        "last_sync": "2025-02-17T23:47:47Z"
      },
      "schema_version": "1.0.0"
    },
    "last_sync_at": "2025-02-17T23:47:47Z",
    "client_version": 1,
    "force": false,
    "device_id": "test_device"
  }
  ```
- **Response**:
  ```json
  {
    "status": "SUCCESS",
    "server_version": 2,
    "server_data": { ... },
    "sync_metadata": {
      "device_id": "test_device",
      "had_conflicts": false,
      "base_version": 2,
      "changes": []
    },
    "is_cloud_synced": true,
    "last_sync_at": "2025-02-17T23:47:47Z"
  }
  ```

### Get Sync Status
- **Endpoint**: `GET /api/v1/portfolios/{portfolio_id}/sync/status`
- **Description**: Get sync status and detect conflicts
- **Response**:
  ```json
  {
    "is_synced": true,
    "last_sync_at": "2025-02-17T23:47:47Z",
    "server_version": 2,
    "last_sync_device": "test_device",
    "had_conflicts": false,
    "pending_changes": 0
  }
  ```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "This feature requires a premium subscription"
}
```

### 404 Not Found
```json
{
  "detail": "Portfolio not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Testing with cURL

### Authentication
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"

# Get Current User
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Portfolios
```bash
# Create Portfolio
curl -X POST http://localhost:8000/api/v1/portfolios/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @portfolio.json

# Get All Portfolios
curl http://localhost:8000/api/v1/portfolios/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Sync Portfolio
curl -X POST http://localhost:8000/api/v1/portfolios/1/sync \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @sync.json
```
