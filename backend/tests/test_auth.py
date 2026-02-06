"""
Unit tests for authentication utilities
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException
from database import User
from utils.auth import AuthManager, encrypt_aws_credentials, decrypt_aws_credentials


class TestAuthManager:
    """Test AuthManager class"""
    
    def test_verify_password(self):
        """Test password verification"""
        password = "TestPassword123!"
        hashed = AuthManager.get_password_hash(password)
        assert AuthManager.verify_password(password, hashed) is True
        assert AuthManager.verify_password("wrong_password", hashed) is False
    
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "1", "email": "test@example.com"}
        token = AuthManager.create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "1", "email": "test@example.com"}
        token = AuthManager.create_refresh_token(data)
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_token_valid(self):
        """Test token verification with valid token"""
        data = {"sub": "1", "email": "test@example.com"}
        token = AuthManager.create_access_token(data)
        payload = AuthManager.verify_token(token, "access")
        assert payload["sub"] == "1"
        assert payload["email"] == "test@example.com"
    
    def test_verify_token_expired(self):
        """Test token verification with expired token"""
        data = {"sub": "1", "email": "test@example.com"}
        token = AuthManager.create_access_token(data, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc_info:
            AuthManager.verify_token(token, "access")
        assert exc_info.value.status_code == 401
    
    def test_verify_token_wrong_type(self):
        """Test token verification with wrong token type"""
        data = {"sub": "1", "email": "test@example.com"}
        token = AuthManager.create_refresh_token(data)
        with pytest.raises(HTTPException) as exc_info:
            AuthManager.verify_token(token, "access")
        assert exc_info.value.status_code == 401
    
    def test_get_user_from_token(self, db_session, sample_user_data):
        """Test getting user from token"""
        # Create user
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=AuthManager.get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        # Create token
        token = AuthManager.create_access_token({"sub": str(user.id)})
        
        # Get user from token
        retrieved_user = AuthManager.get_user_from_token(db_session, token)
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email


class TestCredentialEncryption:
    """Test AWS credential encryption/decryption"""
    
    def test_encrypt_decrypt_credentials(self):
        """Test credential encryption and decryption"""
        access_key = "AKIAIOSFODNN7EXAMPLE"
        secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        
        encrypted_access, encrypted_secret = encrypt_aws_credentials(access_key, secret_key)
        
        # Encrypted values should be different from original
        assert encrypted_access != access_key
        assert encrypted_secret != secret_key
        
        # Decryption should recover original values
        decrypted_access, decrypted_secret = decrypt_aws_credentials(encrypted_access, encrypted_secret)
        assert decrypted_access == access_key
        assert decrypted_secret == secret_key
