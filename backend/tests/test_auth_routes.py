"""
Integration tests for authentication routes
"""
import pytest
from database import User
from utils.auth import AuthManager


class TestAuthRoutes:
    """Test authentication API endpoints"""
    
    def test_register_user(self, client, sample_user_data):
        """Test user registration"""
        response = client.post(
            "/api/auth/register",
            json=sample_user_data
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == sample_user_data["email"]
    
    def test_register_duplicate_email(self, client, sample_user_data):
        """Test registration with duplicate email"""
        # Register first user
        client.post("/api/auth/register", json=sample_user_data)
        
        # Try to register again with same email
        response = client.post(
            "/api/auth/register",
            json=sample_user_data
        )
        assert response.status_code == 400
    
    def test_login_user(self, client, db_session, sample_user_data):
        """Test user login"""
        # Create user first
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=AuthManager.get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client, db_session, sample_user_data):
        """Test getting current user info"""
        # Create and login user
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=AuthManager.get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        token = AuthManager.create_access_token({"sub": str(user.id)})
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == 403
