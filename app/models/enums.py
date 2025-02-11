from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"

# Feature limits for different tiers
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "max_portfolios": 1,
        "max_alerts": 3,
        "refresh_rate_seconds": 300,  # 5 minutes
        "historical_data_days": 30,
        "cloud_storage": False,
        "api_access": False,
        "advanced_analytics": False,
        "exchange_integration": False,
    },
    SubscriptionTier.PREMIUM: {
        "max_portfolios": float('inf'),
        "max_alerts": float('inf'),
        "refresh_rate_seconds": 60,  # 1 minute
        "historical_data_days": 365,
        "cloud_storage": True,
        "api_access": True,
        "advanced_analytics": True,
        "exchange_integration": True,
    }
}
