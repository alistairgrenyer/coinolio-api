from pydantic_settings import BaseSettings
from functools import lru_cache
from datetime import timedelta

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Coinolio API"
    API_PORT: int = 3000
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Stripe Configuration
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PREMIUM_PRICE_ID: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:3000/subscription/success"
    STRIPE_CANCEL_URL: str = "http://localhost:3000/subscription/cancel"
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "coinolio"
    SQLALCHEMY_DATABASE_URI: str = ""

    def _build_db_uri(self) -> str:
        """Build database URI from components"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}/{self.POSTGRES_DB}"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CoinGecko Configuration
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"
    COINGECKO_API_KEY: str = ""  # Optional, for higher rate limits
    
    # Cache Configuration
    CACHE_EXPIRE_MINUTES: int = 5
    
    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SQLALCHEMY_DATABASE_URI = self._build_db_uri()

@lru_cache()
def get_settings() -> Settings:
    return Settings()
