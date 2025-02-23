from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, coins, portfolios, subscriptions
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Coinolio API",
    description="Crypto portfolio tracking API with CoinGecko integration",
    version="1.0.0"
)

# Configure CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"]
)

app.include_router(
    portfolios.router,
    prefix=f"{settings.API_V1_STR}/portfolios",
    tags=["portfolios"]
)

app.include_router(
    subscriptions.router,
    prefix=f"{settings.API_V1_STR}/subscriptions",
    tags=["subscriptions"]
)

app.include_router(
    coins.router,
    prefix=f"{settings.API_V1_STR}/coins",
    tags=["coins"]
)

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Check if the service is healthy"""
    return {"status": "healthy"}
