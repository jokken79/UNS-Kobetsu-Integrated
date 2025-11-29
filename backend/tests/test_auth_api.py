"""
Authentication API Tests - /api/v1/auth endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import verify_password


class TestAuthAPI:
    """Test suite for authentication endpoints."""

    def test_login_successful(self, client: TestClient, test_user: User):
        """Test successful login with valid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login fails with incorrect password."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_user_not_found(self, client: TestClient):
        """Test login fails with non-existent user."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "testpassword"
        })
        
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_inactive_user(self, client: TestClient, test_inactive_user: User):
        """Test login fails for inactive user."""
        response = client.post("/api/v1/auth/login", json={
            "email": "inactive@example.com",
            "password": "testpassword"
        })
        
        assert response.status_code == 400
        assert "Inactive" in response.json()["detail"]

    def test_get_current_user(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test retrieving current user information."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["role"] == test_user.role
        assert data["is_active"] is True

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test /me endpoint requires authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code in [401, 403]

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test /me endpoint with invalid token."""
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid_token_here"
        })
        
        assert response.status_code in [401, 403]

    def test_register_user_success(self, client: TestClient, db: Session):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User",
            "role": "user"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["role"] == "user"
        assert data["is_active"] is True
        
        # Verify user was created in database
        from app.models.user import User
        user = db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.full_name == "New User"

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration fails with duplicate email."""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",  # Already exists
            "password": "password123",
            "full_name": "Duplicate User"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_weak_password(self, client: TestClient):
        """Test registration fails with weak password."""
        response = client.post("/api/v1/auth/register", json={
            "email": "weakpass@example.com",
            "password": "short",  # Less than 8 characters
            "full_name": "Weak Password User"
        })
        
        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["detail"]

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test token refresh with valid refresh token."""
        # First login to get tokens
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new tokens
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh fails with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_refresh_token"
        })
        
        assert response.status_code in [401, 403, 422]

    def test_change_password_success(self, client: TestClient, auth_headers: dict, db: Session, test_user: User):
        """Test successful password change."""
        response = client.post("/api/v1/auth/change-password", 
            headers=auth_headers,
            json={
                "current_password": "testpassword",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        assert "success" in response.json()["message"]
        
        # Verify password was actually changed
        db.refresh(test_user)
        assert verify_password("newpassword123", test_user.hashed_password)

    def test_change_password_wrong_current(self, client: TestClient, auth_headers: dict):
        """Test password change fails with wrong current password."""
        response = client.post("/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    def test_change_password_weak_new(self, client: TestClient, auth_headers: dict):
        """Test password change fails with weak new password."""
        response = client.post("/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "testpassword",
                "new_password": "short"
            }
        )
        
        assert response.status_code == 400
        assert "at least 8 characters" in response.json()["detail"]

    def test_change_password_unauthorized(self, client: TestClient):
        """Test password change requires authentication."""
        response = client.post("/api/v1/auth/change-password", json={
            "current_password": "testpassword",
            "new_password": "newpassword123"
        })
        
        assert response.status_code in [401, 403]

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    def test_logout_unauthorized(self, client: TestClient):
        """Test logout requires authentication."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code in [401, 403]
