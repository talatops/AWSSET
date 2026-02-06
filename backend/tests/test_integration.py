"""
Integration tests for API endpoints
"""
import pytest
from database import User
from utils.auth import AuthManager


class TestAuthIntegration:
    """Integration tests for authentication flow"""
    
    def test_register_login_flow(self, client):
        """Test complete registration and login flow"""
        # Register
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
        
        register_response = client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201
        assert "access_token" in register_response.json()
        
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={"email": register_data["email"], "password": register_data["password"]}
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        # Get current user
        token = login_response.json()["access_token"]
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == register_data["email"]
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == 403
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
