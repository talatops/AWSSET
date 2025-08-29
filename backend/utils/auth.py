"""
Authentication utilities for AWS Chatbot
JWT token management and OAuth integration
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from decouple import config
import requests
import secrets
import hashlib

from database import get_db, User
from utils.logger import get_auth_logger

logger = get_auth_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_ALGORITHM = config("JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
REFRESH_TOKEN_EXPIRE_MINUTES = config("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", default=10080, cast=int)

# OAuth Configuration
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")
PROTON_CLIENT_ID = config("PROTON_CLIENT_ID", default="")
PROTON_CLIENT_SECRET = config("PROTON_CLIENT_SECRET", default="")

# Security
security = HTTPBearer()

class AuthManager:
    """Centralized authentication management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        logger.info(f"Access token created for user: {data.get('sub')}")
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        logger.info(f"Refresh token created for user: {data.get('sub')}")
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"JWT validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    def get_user_from_token(db: Session, token: str) -> User:
        """Get user from JWT token"""
        payload = AuthManager.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user

class GoogleOAuth:
    """Google OAuth integration"""
    
    GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    @staticmethod
    def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "client_id": GoogleOAuth.GOOGLE_CLIENT_ID,
            "client_secret": GoogleOAuth.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        
        try:
            logger.info(f"Attempting to exchange Google code for token with client_id: {GoogleOAuth.GOOGLE_CLIENT_ID[:10]}...")
            response = requests.post(GoogleOAuth.GOOGLE_TOKEN_URL, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully exchanged Google authorization code for token")
            return token_data
        except requests.Timeout:
            logger.error("Timeout while contacting Google OAuth servers")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Timeout while contacting Google OAuth servers"
            )
        except requests.RequestException as e:
            logger.error(f"Failed to exchange Google code for token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Google response: {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange authorization code: {str(e)}"
            )
    
    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = requests.get(GoogleOAuth.GOOGLE_USER_INFO_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            user_info = response.json()
            logger.info(f"Successfully retrieved Google user info for: {user_info.get('email')}")
            return user_info
        except requests.Timeout:
            logger.error("Timeout while getting Google user info")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Timeout while getting user information from Google"
            )
        except requests.RequestException as e:
            logger.error(f"Failed to get Google user info: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Google response: {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get user information: {str(e)}"
            )

class ProtonOAuth:
    """Proton Mail OAuth integration (if supported on free tier)"""
    
    PROTON_CLIENT_ID = PROTON_CLIENT_ID
    PROTON_CLIENT_SECRET = PROTON_CLIENT_SECRET
    # Note: Proton's OAuth endpoints (may not be available on free tier)
    PROTON_TOKEN_URL = "https://account.proton.me/api/auth/v4/token"
    PROTON_USER_INFO_URL = "https://account.proton.me/api/auth/v4/userinfo"
    
    @staticmethod
    def is_available() -> bool:
        """Check if Proton OAuth is configured and available"""
        return bool(ProtonOAuth.PROTON_CLIENT_ID and ProtonOAuth.PROTON_CLIENT_SECRET)
    
    @staticmethod
    def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if not ProtonOAuth.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Proton OAuth not configured or available on free tier"
            )
        
        data = {
            "client_id": ProtonOAuth.PROTON_CLIENT_ID,
            "client_secret": ProtonOAuth.PROTON_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        
        try:
            response = requests.post(ProtonOAuth.PROTON_TOKEN_URL, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            logger.info("Successfully exchanged Proton authorization code for token")
            return token_data
        except requests.RequestException as e:
            logger.error(f"Failed to exchange Proton code for token: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code with Proton"
            )
    
    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, Any]:
        """Get user information from Proton"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = requests.get(ProtonOAuth.PROTON_USER_INFO_URL, headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            logger.info(f"Successfully retrieved Proton user info for: {user_info.get('email')}")
            return user_info
        except requests.RequestException as e:
            logger.error(f"Failed to get Proton user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from Proton"
            )

def generate_state_token() -> str:
    """Generate a secure state token for OAuth"""
    return secrets.token_urlsafe(32)

def verify_state_token(received_state: str, stored_state: str) -> bool:
    """Verify OAuth state token"""
    return secrets.compare_digest(received_state, stored_state)

def create_user_session(db: Session, user: User) -> Dict[str, str]:
    """Create user session with access and refresh tokens"""
    token_data = {"sub": str(user.id), "email": user.email, "username": user.username}
    
    access_token = AuthManager.create_access_token(token_data)
    refresh_token = AuthManager.create_refresh_token(token_data)
    
    logger.info(f"User session created for: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return AuthManager.get_user_from_token(db, token)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def encrypt_aws_credentials(access_key: str, secret_key: str) -> tuple[str, str]:
    """Encrypt AWS credentials for secure storage"""
    # Simple encryption using app secret (in production, use proper encryption)
    salt = JWT_SECRET_KEY.encode()
    
    encrypted_access = hashlib.pbkdf2_hmac('sha256', access_key.encode(), salt, 100000).hex()
    encrypted_secret = hashlib.pbkdf2_hmac('sha256', secret_key.encode(), salt, 100000).hex()
    
    return encrypted_access, encrypted_secret

def decrypt_aws_credentials(encrypted_access: str, encrypted_secret: str) -> tuple[str, str]:
    """Decrypt AWS credentials for use"""
    # Note: This is a simplified approach. In production, use proper encryption/decryption
    # For now, we'll store credentials securely and retrieve them as needed
    # This is a placeholder - actual implementation would use reversible encryption
    logger.warning("AWS credential decryption called - implement proper encryption in production")
    return encrypted_access, encrypted_secret
