"""
Authentication router for AWS Chatbot
Handles login, registration, OAuth, and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
import jwt
from datetime import datetime

from database import get_db, User
from utils.auth import (
    AuthManager, GoogleOAuth, ProtonOAuth, 
    create_user_session, generate_state_token, verify_state_token,
    get_current_user, get_current_active_user
)
from utils.logger import get_auth_logger, log_security_event
from utils.config import AppConfig

logger = get_auth_logger()
router = APIRouter()

# Pydantic models for request/response
class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class OAuthCallback(BaseModel):
    code: str
    state: str
    provider: str

class UserProfile(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    provider: str
    is_active: bool
    is_verified: bool
    profile_customized: bool
    aws_region: str
    created_at: datetime

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    aws_region: Optional[str] = None

import json
import os
from pathlib import Path

import redis
from utils.config import AppConfig

# OAuth state storage (Redis first, file-based fallback)
STATE_FILE = Path("/tmp/oauth_states.json")

def _get_redis_client():
    """Create a Redis client for OAuth state and token management."""
    try:
        return redis.from_url(AppConfig.REDIS_URL, decode_responses=True)
    except Exception as e:
        logger.warning(f"Redis not available for OAuth state storage: {e}")
        return None

redis_client = _get_redis_client()

def _oauth_state_key(state: str) -> str:
    return f"oauth_state:{state}"

def get_oauth_states():
    """Get all OAuth states (primarily for debugging)."""
    # Prefer Redis if available
    if redis_client:
        try:
            keys = redis_client.keys(_oauth_state_key("*"))
            states = {}
            for key in keys:
                raw = redis_client.get(key)
                if not raw:
                    continue
                try:
                    state_id = key.split("oauth_state:")[1]
                    states[state_id] = json.loads(raw)
                except Exception:
                    continue
            return states
        except Exception as e:
            logger.error(f"Failed to read OAuth states from Redis: {e}")
    # Fallback to file-based storage
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def get_oauth_state(state: str):
    """Get a single OAuth state."""
    if redis_client:
        try:
            raw = redis_client.get(_oauth_state_key(state))
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.error(f"Failed to get OAuth state from Redis: {e}")
    # Fallback to file
    states = get_oauth_states()
    return states.get(state)

def save_oauth_state(state, data):
    """Save OAuth state (Redis with TTL, file fallback)."""
    if redis_client:
        try:
            # Store state for 10 minutes by default
            redis_client.setex(_oauth_state_key(state), 600, json.dumps(data))
            return
        except Exception as e:
            logger.error(f"Failed to save OAuth state to Redis, falling back to file: {e}")
    try:
        states = get_oauth_states()
        states[state] = data
        with open(STATE_FILE, "w") as f:
            json.dump(states, f)
    except Exception as e:
        logger.error(f"Failed to save OAuth state: {e}")

def remove_oauth_state(state):
    """Remove OAuth state."""
    if redis_client:
        try:
            redis_client.delete(_oauth_state_key(state))
        except Exception as e:
            logger.error(f"Failed to remove OAuth state from Redis: {e}")
    try:
        states = get_oauth_states()
        if state in states:
            del states[state]
            with open(STATE_FILE, "w") as f:
                json.dump(states, f)
    except Exception as e:
        logger.error(f"Failed to remove OAuth state: {e}")

@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """Register a new user with email and password"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        log_security_event(logger, "registration_attempt_duplicate", details={"email": user_data.email})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = AuthManager.get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        provider="local",
        is_active=True,
        is_verified=False  # Email verification can be added later
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create session
    tokens = create_user_session(db, new_user)
    
    log_security_event(logger, "user_registered", user_id=str(new_user.id), details={"email": user_data.email})
    
    return {
        **tokens,
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
            "full_name": new_user.full_name,
            "provider": new_user.provider
        }
    }

@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Login user with email and password"""
    
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not AuthManager.verify_password(user_data.password, user.hashed_password):
        log_security_event(
            logger, "login_attempt_failed", 
            ip_address=request.client.host,
            details={"email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated"
        )
    
    # Create session
    tokens = create_user_session(db, user)
    
    log_security_event(
        logger, "user_login_success", 
        user_id=str(user.id),
        ip_address=request.client.host
    )
    
    return {
        **tokens,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "provider": user.provider
        }
    }

@router.get("/oauth/google")
async def google_oauth_init():
    """Initialize Google OAuth flow"""
    if not GoogleOAuth.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured"
        )
    
    state = generate_state_token()
    save_oauth_state(state, {"provider": "google", "created_at": datetime.utcnow().isoformat()})
    
    # Google OAuth URL
    redirect_uri = AppConfig.GOOGLE_REDIRECT_URI
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GoogleOAuth.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid email profile&"
        f"response_type=code&"
        f"state={state}"
    )
    
    logger.info(f"Google OAuth flow initiated with state: {state}")
    
    return {"auth_url": google_auth_url, "state": state}

@router.get("/oauth/proton")
async def proton_oauth_init():
    """Initialize Proton OAuth flow (if available)"""
    if not ProtonOAuth.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Proton OAuth not available or configured. This may not be supported on the free tier."
        )
    
    state = generate_state_token()
    save_oauth_state(state, {"provider": "proton", "created_at": datetime.utcnow().isoformat()})
    
    # Proton OAuth URL (may not work on free tier)
    redirect_uri = AppConfig.PROTON_REDIRECT_URI
    proton_auth_url = (
        f"https://account.proton.me/oauth/authorize?"
        f"client_id={ProtonOAuth.PROTON_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=mail.read user.read&"
        f"response_type=code&"
        f"state={state}"
    )
    
    logger.info(f"Proton OAuth flow initiated with state: {state}")
    
    return {"auth_url": proton_auth_url, "state": state}

@router.get("/oauth/callback")
async def oauth_callback_debug():
    """Debug endpoint to show OAuth callback status"""
    oauth_states = get_oauth_states()
    return {
        "message": "OAuth callback endpoint",
        "method": "This endpoint expects POST requests with JSON data",
        "stored_states": list(oauth_states.keys()),
        "example": {
            "code": "authorization_code_from_google",
            "state": "state_token_from_oauth_init",
            "provider": "google"
        }
    }

@router.post("/oauth/callback", response_model=TokenResponse)
async def oauth_callback(callback_data: OAuthCallback, db: Session = Depends(get_db)):
    """Handle OAuth callback from Google or Proton"""
    
    # Verify state token
    oauth_states = get_oauth_states()
    stored_state = oauth_states.get(callback_data.state)
    if not stored_state or stored_state["provider"] != callback_data.provider:
        log_security_event(logger, "oauth_invalid_state", details={
            "received_state": callback_data.state,
            "provider": callback_data.provider,
            "available_states": list(oauth_states.keys())
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state parameter. Received: {callback_data.state[:10]}..."
        )
    
    # Clean up state
    remove_oauth_state(callback_data.state)
    
    try:
        # Exchange code for token based on provider
        if callback_data.provider == "google":
            redirect_uri = AppConfig.GOOGLE_REDIRECT_URI
            token_data = GoogleOAuth.exchange_code_for_token(callback_data.code, redirect_uri)
            user_info = GoogleOAuth.get_user_info(token_data["access_token"])
            
        elif callback_data.provider == "proton":
            redirect_uri = AppConfig.PROTON_REDIRECT_URI
            token_data = ProtonOAuth.exchange_code_for_token(callback_data.code, redirect_uri)
            user_info = ProtonOAuth.get_user_info(token_data["access_token"])
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported OAuth provider"
            )
        
        # Find or create user
        user = db.query(User).filter(
            User.email == user_info["email"],
            User.provider == callback_data.provider
        ).first()
        
        if not user:
            # Create new user from OAuth
            user = User(
                email=user_info["email"],
                username=user_info.get("email", "").split("@")[0],
                full_name=user_info.get("name"),
                provider=callback_data.provider,
                provider_id=user_info.get("id"),
                is_active=True,
                is_verified=True,  # OAuth users are considered verified
                profile_customized=False  # New users haven't customized yet
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            log_security_event(logger, "oauth_user_created", user_id=str(user.id), details={
                "provider": callback_data.provider,
                "email": user_info["email"]
            })
        else:
            # Update OAuth user info ONLY if profile hasn't been customized
            if not user.profile_customized:
                updated = False
                oauth_full_name = user_info.get("name")
                
                # Only update if OAuth provides better data than what we have
                if oauth_full_name and oauth_full_name != user.full_name:
                    user.full_name = oauth_full_name
                    updated = True
                
                if updated:
                    user.updated_at = datetime.utcnow()
                    db.commit()
                    db.refresh(user)
                    
                    log_security_event(logger, "oauth_user_profile_updated", user_id=str(user.id), details={
                        "provider": callback_data.provider,
                        "updated_fields": ["full_name"] if oauth_full_name else []
                    })
            
            log_security_event(logger, "oauth_user_login", user_id=str(user.id), details={
                "provider": callback_data.provider,
                "profile_customized": user.profile_customized
            })
        
        # Create session
        tokens = create_user_session(db, user)
        
        return {
            **tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "provider": user.provider
            }
        }
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    
    try:
        # Verify refresh token
        payload = AuthManager.verify_token(token_data.refresh_token, "refresh")
        user_id = payload.get("sub")
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new session
        tokens = create_user_session(db, user)
        
        log_security_event(logger, "token_refreshed", user_id=str(user.id))
        
        return {
            **tokens,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "provider": user.provider
            }
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        provider=current_user.provider,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        profile_customized=current_user.profile_customized,
        aws_region=current_user.aws_region,
        created_at=current_user.created_at
    )

@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    profile_data: ProfileUpdate, 
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    updated_fields = []
    
    # Update username if provided and different
    if profile_data.username and profile_data.username != current_user.username:
        # Check if username is already taken
        existing_user = db.query(User).filter(
            User.username == profile_data.username,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken"
            )
        
        current_user.username = profile_data.username
        updated_fields.append("username")
    
    # Update full name if provided
    if profile_data.full_name is not None and profile_data.full_name != current_user.full_name:
        current_user.full_name = profile_data.full_name
        updated_fields.append("full_name")
    
    # Update AWS region if provided
    if profile_data.aws_region and profile_data.aws_region != current_user.aws_region:
        current_user.aws_region = profile_data.aws_region
        updated_fields.append("aws_region")
    
    # Mark profile as customized if any updates were made
    if updated_fields:
        current_user.profile_customized = True
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        log_security_event(logger, "user_profile_updated", user_id=str(current_user.id), details={
            "updated_fields": updated_fields
        })
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        provider=current_user.provider,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        profile_customized=current_user.profile_customized,
        aws_region=current_user.aws_region,
        created_at=current_user.created_at
    )

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    """Logout user and invalidate the current access token via a blacklist."""
    token = credentials.credentials

    # Blacklist the token using Redis if available so it cannot be reused
    if redis_client:
        try:
            # Decode without verifying signature/expiry to extract exp
            decoded = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
            exp_timestamp = decoded.get("exp")
            ttl = max(int(exp_timestamp - datetime.utcnow().timestamp()), 0) if exp_timestamp else 0
            blacklist_key = f"jwt_blacklist:{token}"
            redis_client.set(blacklist_key, "1")
            if ttl > 0:
                redis_client.expire(blacklist_key, ttl)
        except Exception as e:
            logger.error(f"Failed to blacklist JWT on logout: {e}")

    log_security_event(logger, "user_logout", user_id=str(current_user.id))
    return {"message": "Successfully logged out"}

@router.get("/oauth/status")
async def oauth_status():
    """Get OAuth provider availability status"""
    return {
        "google": {
            "available": bool(GoogleOAuth.GOOGLE_CLIENT_ID),
            "configured": bool(GoogleOAuth.GOOGLE_CLIENT_ID and GoogleOAuth.GOOGLE_CLIENT_SECRET)
        },
        "proton": {
            "available": ProtonOAuth.is_available(),
            "configured": bool(ProtonOAuth.PROTON_CLIENT_ID and ProtonOAuth.PROTON_CLIENT_SECRET),
            "note": "Proton OAuth may not be available on free tier accounts"
        }
    }
