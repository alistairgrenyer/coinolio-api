from typing import Dict, Any
from datetime import datetime, timedelta

def create_mock_checkout_session(
    customer_id: str,
    subscription_id: str,
    user_id: int
) -> Dict[str, Any]:
    """Create a mock Stripe checkout session"""
    return {
        "id": "cs_test_mock",
        "object": "checkout.session",
        "customer": customer_id,
        "subscription": subscription_id,
        "client_reference_id": str(user_id),
        "payment_status": "paid",
        "url": "https://checkout.stripe.com/mock"
    }

def create_mock_subscription(
    customer_id: str,
    subscription_id: str,
    status: str = "active"
) -> Dict[str, Any]:
    """Create a mock Stripe subscription"""
    now = datetime.utcnow()
    return {
        "id": subscription_id,
        "object": "subscription",
        "customer": customer_id,
        "status": status,
        "current_period_start": int(now.timestamp()),
        "current_period_end": int((now + timedelta(days=30)).timestamp()),
        "cancel_at_period_end": False,
        "items": {
            "data": [{
                "id": "si_mock",
                "object": "subscription_item",
                "price": {
                    "id": "price_mock",
                    "product": "prod_mock"
                }
            }]
        }
    }

def create_mock_customer(customer_id: str, email: str) -> Dict[str, Any]:
    """Create a mock Stripe customer"""
    return {
        "id": customer_id,
        "object": "customer",
        "email": email,
        "created": int(datetime.utcnow().timestamp()),
        "subscriptions": {
            "data": []
        }
    }

def create_mock_webhook_event(
    event_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a mock Stripe webhook event"""
    return {
        "id": "evt_mock",
        "object": "event",
        "type": event_type,
        "created": int(datetime.utcnow().timestamp()),
        "data": {
            "object": data
        },
        "livemode": False
    }
