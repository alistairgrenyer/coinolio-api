import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.enums import SubscriptionTier

def test_create_checkout_session_unauthorized(client: TestClient):
    """Test creating checkout session without authentication"""
    response = client.post("/api/v1/subscriptions/create-checkout-session")
    assert response.status_code == 401

def test_create_checkout_session_already_premium(
    client: TestClient,
    premium_user_token: str
):
    """Test creating checkout session when already premium"""
    response = client.post(
        "/api/v1/subscriptions/create-checkout-session",
        headers={"Authorization": f"Bearer {premium_user_token}"}
    )
    assert response.status_code == 400
    assert "already have a premium subscription" in response.json()["detail"]

@patch("stripe.checkout.Session.create")
def test_create_checkout_session_success(
    mock_create_session,
    client: TestClient,
    normal_user_token: str
):
    """Test successful checkout session creation"""
    # Mock Stripe response
    mock_create_session.return_value = MagicMock(
        id="cs_test123",
        url="https://checkout.stripe.com/test"
    )

    response = client.post(
        "/api/v1/subscriptions/create-checkout-session",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    
    assert response.status_code == 200
    assert "checkout_url" in response.json()
    assert response.json()["checkout_url"] == "https://checkout.stripe.com/test"

@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_invalid_signature(
    mock_construct_event,
    client: TestClient
):
    """Test webhook with invalid signature"""
    mock_construct_event.side_effect = ValueError("Invalid signature")
    
    response = client.post(
        "/api/v1/subscriptions/webhook",
        headers={"Stripe-Signature": "invalid"},
        json={"type": "checkout.session.completed"}
    )
    
    assert response.status_code == 400
    assert "Invalid signature" in response.json()["detail"]

@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_checkout_completed(
    mock_construct_event,
    client: TestClient,
    db: Session,
    normal_user: User
):
    """Test successful checkout completion webhook"""
    # Mock the Stripe event
    mock_event = MagicMock(
        type="checkout.session.completed",
        data=MagicMock(
            object=MagicMock(
                customer="cus_test123",
                subscription="sub_test123",
                client_reference_id=str(normal_user.id)
            )
        )
    )
    mock_construct_event.return_value = mock_event

    response = client.post(
        "/api/v1/subscriptions/webhook",
        headers={"Stripe-Signature": "valid"},
        json={"type": "checkout.session.completed"}
    )
    
    assert response.status_code == 200
    
    # Verify user was updated
    db.refresh(normal_user)
    assert normal_user.subscription_tier == SubscriptionTier.PREMIUM
    assert normal_user.stripe_customer_id == "cus_test123"
    assert normal_user.stripe_subscription_id == "sub_test123"

@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_subscription_deleted(
    mock_construct_event,
    client: TestClient,
    db: Session,
    premium_user: User
):
    """Test subscription cancellation webhook"""
    # Mock the Stripe event
    mock_event = MagicMock(
        type="customer.subscription.deleted",
        data=MagicMock(
            object=MagicMock(
                customer=premium_user.stripe_customer_id
            )
        )
    )
    mock_construct_event.return_value = mock_event

    response = client.post(
        "/api/v1/subscriptions/webhook",
        headers={"Stripe-Signature": "valid"},
        json={"type": "customer.subscription.deleted"}
    )
    
    assert response.status_code == 200
    
    # Verify user was downgraded
    db.refresh(premium_user)
    assert premium_user.subscription_tier == SubscriptionTier.FREE
    assert premium_user.stripe_subscription_id is None

def test_get_subscription_status_unauthorized(client: TestClient):
    """Test getting subscription status without authentication"""
    response = client.get("/api/v1/subscriptions/status")
    assert response.status_code == 401

def test_get_subscription_status_free_user(
    client: TestClient,
    normal_user_token: str
):
    """Test getting subscription status for free user"""
    response = client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "FREE"
    assert data["is_premium"] is False

def test_get_subscription_status_premium_user(
    client: TestClient,
    premium_user_token: str
):
    """Test getting subscription status for premium user"""
    response = client.get(
        "/api/v1/subscriptions/status",
        headers={"Authorization": f"Bearer {premium_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "PREMIUM"
    assert data["is_premium"] is True
    assert "stripe_customer_id" in data
    assert "stripe_subscription_id" in data

@patch("stripe.Subscription.modify")
def test_cancel_subscription_success(
    mock_modify,
    client: TestClient,
    premium_user_token: str
):
    """Test successful subscription cancellation"""
    response = client.post(
        "/api/v1/subscriptions/cancel",
        headers={"Authorization": f"Bearer {premium_user_token}"}
    )
    
    assert response.status_code == 200
    assert mock_modify.called
    data = response.json()
    assert data["message"] == "Subscription cancelled successfully"

def test_cancel_subscription_free_user(
    client: TestClient,
    normal_user_token: str
):
    """Test cancelling non-existent subscription"""
    response = client.post(
        "/api/v1/subscriptions/cancel",
        headers={"Authorization": f"Bearer {normal_user_token}"}
    )
    
    assert response.status_code == 400
    assert "No active subscription" in response.json()["detail"]
