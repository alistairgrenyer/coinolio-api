from datetime import datetime
from typing import Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.core.config import get_settings
from app.db.base import get_db
from app.models.enums import SubscriptionTier
from app.models.user import User

settings = get_settings()
stripe.api_key = settings.STRIPE_API_KEY

router = APIRouter()

class SubscriptionStatus(BaseModel):
    tier: SubscriptionTier
    is_active: bool
    expires_at: datetime | None = None
    next_billing_date: datetime | None = None

@router.post("/create-checkout-session")
async def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Create a Stripe checkout session for premium subscription"""
    
    # Create or get Stripe customer
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={"user_id": current_user.id}
        )
        current_user.stripe_customer_id = customer.id
        db.commit()
    
    # Create checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price": settings.STRIPE_PREMIUM_PRICE_ID,
            "quantity": 1,
        }],
        mode="subscription",
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        metadata={
            "user_id": current_user.id
        }
    )
    
    return {"checkout_url": checkout_session.url}

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """Handle Stripe webhooks for subscription events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        user = db.query(User).filter(
            User.stripe_customer_id == subscription.customer
        ).first()
        
        if user:
            user.subscription_tier = SubscriptionTier.PREMIUM
            user.stripe_subscription_id = subscription.id
            user.subscription_expires_at = datetime.fromtimestamp(subscription.current_period_end)
            db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        user = db.query(User).filter(
            User.stripe_customer_id == subscription.customer
        ).first()
        
        if user:
            user.subscription_tier = SubscriptionTier.FREE
            user.stripe_subscription_id = None
            user.subscription_expires_at = None
            db.commit()
    
    return {"status": "success"}

@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user's subscription status"""
    
    status = SubscriptionStatus(
        tier=current_user.subscription_tier,
        is_active=True,
        expires_at=current_user.subscription_expires_at
    )
    
    # Get next billing date from Stripe if premium
    if current_user.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(current_user.stripe_subscription_id)
            status.next_billing_date = datetime.fromtimestamp(subscription.current_period_end)
        except stripe.error.StripeError:
            pass
    
    return status

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Cancel premium subscription"""
    if not current_user.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found"
        )
    
    try:
        # Cancel at period end
        stripe.Subscription.modify(
            current_user.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        return {"message": "Subscription will be cancelled at the end of the billing period"}
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
