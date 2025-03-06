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
- **Endpoint**: `POST /api/v1/portfolios`
- **Description**: Create a new portfolio
- **Request Body**:
  ```json
  {
    "name": "My Portfolio",
    "data": {
      "assets": {
        "bitcoin": {
          "amount": "1.5",
          "cost_basis": "35000.00"
        }
      }
    },
    "device_id": "device_123"  // Optional
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "user_id": 1,
    "name": "My Portfolio",
    "data": {
      "assets": {
        "bitcoin": {
          "amount": "1.5",
          "cost_basis": "35000.00"
        }
      }
    },
    "version": 1,
    "is_cloud_synced": true,
    "last_sync_at": "2025-03-06T18:31:58Z",
    "last_sync_device": "device_123"
  }
  ```

### Get All Portfolios
- **Endpoint**: `GET /api/v1/portfolios`
- **Description**: Get all portfolios for the current user
- **Response**:
  ```json
  [
    {
      "id": 1,
      "user_id": 1,
      "name": "My Portfolio",
      "data": {
        "assets": {
          "bitcoin": {
            "amount": "1.5",
            "cost_basis": "35000.00"
          }
        }
      },
      "version": 1,
      "is_cloud_synced": true,
      "last_sync_at": "2025-03-06T18:31:58Z",
      "last_sync_device": "device_123"
    }
  ]
  ```

### Get Portfolio
- **Endpoint**: `GET /api/v1/portfolios/{portfolio_id}`
- **Description**: Get a specific portfolio
- **Response**: Same as single portfolio in Get All Portfolios response

### Update Portfolio
- **Endpoint**: `PUT /api/v1/portfolios/{portfolio_id}`
- **Description**: Update a portfolio. When data is updated, the version is incremented and sync metadata is updated.
- **Request Body**:
  ```json
  {
    "name": "Updated Portfolio",  // Optional
    "data": {                    // Optional
      "assets": {
        "bitcoin": {
          "amount": "2.0",
          "cost_basis": "40000.00"
        }
      }
    },
    "device_id": "device_123"    // Optional
  }
  ```
- **Response**: Same as Create Portfolio response

### Sync Portfolio
- **Endpoint**: `POST /api/v1/portfolios/{portfolio_id}/sync`
- **Description**: Sync a portfolio from mobile storage to cloud (Premium feature). Uses last-write-wins strategy with conflict detection.
- **Request Body**:
  ```json
  {
    "client_data": {
      "assets": {
        "bitcoin": {
          "amount": "2.0",
          "cost_basis": "40000.00"
        }
      }
    },
    "last_sync_at": "2025-03-06T18:31:58Z",
    "client_version": 2,
    "device_id": "device_123"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "version": 3,
    "data": {
      "assets": {
        "bitcoin": {
          "amount": "2.0",
          "cost_basis": "40000.00"
        }
      }
    },
    "changes": [
      {
        "type": "modified",
        "path": "assets.bitcoin",
        "value": {
          "amount": "2.0",
          "cost_basis": "40000.00"
        }
      }
    ],
    "last_sync_at": "2025-03-06T18:31:58Z"
  }
  ```

### Get Sync Status
- **Endpoint**: `GET /api/v1/portfolios/{portfolio_id}/sync/status`
- **Description**: Get sync status and detect if conflicts exist
- **Query Parameters**:
  - `client_version` (integer, required): Client's current version
  - `device_id` (string, required): Client device ID
- **Response**:
  ```json
  {
    "needs_sync": true,
    "has_conflicts": false,
    "server_version": 3,
    "server_last_sync": "2025-03-06T18:31:58Z"
  }
  ```

## Coin Endpoints

### Get Coin Prices
- **Endpoint**: `GET /api/v1/coins/prices`
- **Description**: Get current prices for a list of coins. Guest accessible endpoint.
- **Query Parameters**:
  - `ids` (string, required): Comma-separated list of coin ids (e.g., "bitcoin,ethereum")
  - `vs_currency` (string, optional): The target currency of market data (default: "usd")
- **Response**:
  ```json
  [
    {
      "id": "bitcoin",
      "symbol": "btc",
      "name": "Bitcoin",
      "current_price": 65432.10,
      "market_cap": 1234567890,
      "market_cap_rank": 1,
      "price_change_percentage_24h": 2.5,
      "price_change_24h": 1234.56,
      "total_volume": 98765432100
    }
  ]
  ```

### Get Coin Historical Data
- **Endpoint**: `GET /api/v1/coins/historical/{coin_id}`
- **Description**: Get historical price data for a coin. Guest accessible endpoint. Premium users get access to more historical data.
- **Path Parameters**:
  - `coin_id` (string, required): The id of the coin (e.g., "bitcoin")
- **Query Parameters**:
  - `days` (integer, optional): Number of days of historical data (default: 1, max: 365)
  - `vs_currency` (string, optional): The target currency of market data (default: "usd")
- **Response**:
  ```json
  {
    "prices": [
      [1646265600000, 43567.89],  // [timestamp, price]
      [1646352000000, 44123.45]
    ],
    "market_caps": [
      [1646265600000, 824597834563],
      [1646352000000, 835687245789]
    ],
    "total_volumes": [
      [1646265600000, 38475987234],
      [1646352000000, 42356897123]
    ]
  }
  ```
- **Notes**:
  - Free tier users are limited to 7 days of historical data
  - Premium tier users can access up to 365 days of historical data

### Get Trending Coins
- **Endpoint**: `GET /api/v1/coins/trending`
- **Description**: Get trending coins in the last 24 hours. Guest accessible endpoint.
- **Response**:
  ```json
  {
    "coins": [
      {
        "item": {
          "id": "bitcoin",
          "coin_id": 1,
          "name": "Bitcoin",
          "symbol": "BTC",
          "market_cap_rank": 1,
          "thumb": "https://assets.coingecko.com/coins/images/1/thumb/bitcoin.png",
          "small": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png",
          "large": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
          "score": 0
        }
      }
    ]
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
