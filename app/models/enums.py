from enum import Enum
from typing import ClassVar


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class SubscriptionTier(str, Enum):
    GUEST = "guest"
    FREE = "free"
    PREMIUM = "premium"

class TierPrivileges:
    """Defines privileges and limits for each subscription tier"""
    
    # Rate limiting
    RATE_LIMITS: ClassVar[dict[SubscriptionTier, dict[str, int]]] = {
        SubscriptionTier.GUEST: {
            'requests_per_min': 30,
            'concurrent_requests': 5,
            'max_payload_size': 50 * 1024  # 50kb
        },
        SubscriptionTier.FREE: {
            'requests_per_min': 60,
            'concurrent_requests': 10,
            'max_payload_size': 50 * 1024  # 50kb
        },
        SubscriptionTier.PREMIUM: {
            'requests_per_min': 120,
            'concurrent_requests': 20,
            'max_payload_size': 100 * 1024  # 100kb
        }
    }

    # Token expiration times (in minutes)
    ACCESS_TOKEN_EXPIRE_MINUTES: ClassVar[dict[SubscriptionTier, int]] = {
        SubscriptionTier.GUEST: 15,   # 15 minutes
        SubscriptionTier.FREE: 60,    # 1 hour
        SubscriptionTier.PREMIUM: 120  # 2 hours
    }

    # Refresh token expiration times (in days)
    REFRESH_TOKEN_EXPIRE_DAYS: ClassVar[dict[SubscriptionTier, int]] = {
        SubscriptionTier.FREE: 7,     # 7 days
        SubscriptionTier.PREMIUM: 30   # 30 days
    }

    # Portfolio limits
    PORTFOLIO_LIMITS: ClassVar[dict[SubscriptionTier, int]] = {
        SubscriptionTier.GUEST: 0,    # No portfolios for guests
        SubscriptionTier.FREE: 1,     # 1 portfolio for free users
        SubscriptionTier.PREMIUM: 10   # 10 portfolios for premium users
    }

    # Historical data access (in days)
    HISTORICAL_DATA_DAYS: ClassVar[dict[SubscriptionTier, int]] = {
        SubscriptionTier.GUEST: 7,    # 7 days for guests
        SubscriptionTier.FREE: 7,     # 7 days for free users
        SubscriptionTier.PREMIUM: 365  # 365 days for premium users
    }

    @classmethod
    def get_rate_limits(cls, tier: SubscriptionTier) -> dict[str, int]:
        return cls.RATE_LIMITS.get(tier, cls.RATE_LIMITS[SubscriptionTier.GUEST])

    @classmethod
    def get_access_token_expire_minutes(cls, tier: SubscriptionTier) -> int:
        return cls.ACCESS_TOKEN_EXPIRE_MINUTES.get(tier, cls.ACCESS_TOKEN_EXPIRE_MINUTES[SubscriptionTier.GUEST])

    @classmethod
    def get_refresh_token_expire_days(cls, tier: SubscriptionTier) -> int:
        return cls.REFRESH_TOKEN_EXPIRE_DAYS.get(tier, cls.REFRESH_TOKEN_EXPIRE_DAYS[SubscriptionTier.FREE])

    @classmethod
    def get_portfolio_limit(cls, tier: SubscriptionTier) -> int:
        return cls.PORTFOLIO_LIMITS.get(tier, cls.PORTFOLIO_LIMITS[SubscriptionTier.GUEST])

    @classmethod
    def get_historical_data_days(cls, tier: SubscriptionTier) -> int:
        return cls.HISTORICAL_DATA_DAYS.get(tier, cls.HISTORICAL_DATA_DAYS[SubscriptionTier.GUEST])
