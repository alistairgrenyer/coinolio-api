import pytest
from fastapi import status
from datetime import datetime, timedelta
from app.core.config import get_settings
from app.models.user import User
from tests.factories.user import UserFactory

settings = get_settings()

class TestAuthEndpoints:
    def test_register_success(self, client, test_user_data):
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=test_user_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user, test_user_data):
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=test_user_data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Email already registered"

    def test_login_success(self, client, test_user_data):
        # First register a user
        client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=test_user_data
        )
        
        # Then try to login
        response = client.post(
            f"{settings.API_V1_STR}/auth/token",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user_data):
        # First register a user
        client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=test_user_data
        )
        
        # Then try to login with wrong password
        response = client.post(
            f"{settings.API_V1_STR}/auth/token",
            data={
                "username": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Incorrect email or password"

    def test_get_current_user(self, authorized_client, test_user):
        response = authorized_client.get(f"{settings.API_V1_STR}/auth/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["id"] == test_user["id"]

    def test_get_current_user_invalid_token(self, client):
        client.headers["Authorization"] = "Bearer invalid_token"
        response = client.get(f"{settings.API_V1_STR}/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_refresh_token_success(self, client, test_user_data):
        # First register and login to get tokens
        client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=test_user_data
        )
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/token",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Then try to refresh the token
        response = client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            data={"refresh_token": refresh_token}  
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client):
        response = client.post(
            f"{settings.API_V1_STR}/auth/refresh",
            data={"refresh_token": "invalid_token"}  
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid or expired refresh token"
