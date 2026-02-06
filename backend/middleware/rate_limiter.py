"""
Redis-based distributed rate limiting middleware
Supports multiple instances and shared rate limit state
"""

import redis
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import json

from utils.logger import get_security_logger, log_security_event
from utils.config import AppConfig

logger = get_security_logger()


class RedisRateLimiter:
    """Redis-based rate limiter for distributed systems"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                AppConfig.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis rate limiter initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting, falling back to in-memory: {e}")
            self.redis_client = None
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        block_duration: Optional[int] = None
    ) -> tuple[bool, dict]:
        """
        Check if request is within rate limit
        
        Args:
            key: Rate limit key (e.g., IP address or user ID)
            limit: Maximum requests allowed
            window: Time window in seconds
            block_duration: Optional block duration in seconds if limit exceeded
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if not self.redis_client:
            # Fallback: allow request if Redis is unavailable
            return True, {"limit": limit, "remaining": limit, "reset": window}
        
        try:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window)
            
            # Check if IP is blocked
            block_key = f"rate_limit:blocked:{key}"
            if block_duration:
                is_blocked = self.redis_client.get(block_key)
                if is_blocked:
                    reset_time = self.redis_client.ttl(block_key)
                    return False, {
                        "limit": limit,
                        "remaining": 0,
                        "reset": reset_time,
                        "blocked": True
                    }
            
            # Use sliding window log algorithm
            rate_limit_key = f"rate_limit:{key}"
            
            # Remove old entries outside the window
            cutoff = (now - timedelta(seconds=window)).timestamp()
            self.redis_client.zremrangebyscore(rate_limit_key, 0, cutoff)
            
            # Count current requests in window
            current_count = self.redis_client.zcard(rate_limit_key)
            
            if current_count >= limit:
                # Block IP if configured
                if block_duration:
                    self.redis_client.setex(block_key, block_duration, "1")
                    log_security_event(logger, "rate_limit_exceeded_blocked", 
                                     details={"key": key, "limit": limit, "count": current_count})
                
                # Get oldest request timestamp to calculate reset time
                oldest = self.redis_client.zrange(rate_limit_key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1] + window - now.timestamp()) if oldest else window
                
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": reset_time,
                    "count": current_count
                }
            
            # Add current request
            self.redis_client.zadd(rate_limit_key, {str(now.timestamp()): now.timestamp()})
            self.redis_client.expire(rate_limit_key, window)
            
            # Calculate reset time
            oldest = self.redis_client.zrange(rate_limit_key, 0, 0, withscores=True)
            reset_time = int(oldest[0][1] + window - now.timestamp()) if oldest else window
            
            return True, {
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset": reset_time,
                "count": current_count + 1
            }
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open: allow request if Redis fails
            return True, {"limit": limit, "remaining": limit, "reset": window, "error": str(e)}
    
    def get_rate_limit_info(self, key: str, limit: int, window: int) -> dict:
        """Get current rate limit status without incrementing"""
        if not self.redis_client:
            return {"limit": limit, "remaining": limit, "reset": window}
        
        try:
            rate_limit_key = f"rate_limit:{key}"
            now = datetime.utcnow()
            cutoff = (now - timedelta(seconds=window)).timestamp()
            
            # Remove old entries
            self.redis_client.zremrangebyscore(rate_limit_key, 0, cutoff)
            
            # Count current requests
            current_count = self.redis_client.zcard(rate_limit_key)
            
            # Calculate reset time
            oldest = self.redis_client.zrange(rate_limit_key, 0, 0, withscores=True)
            reset_time = int(oldest[0][1] + window - now.timestamp()) if oldest else window
            
            return {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset": reset_time,
                "count": current_count
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit info: {e}")
            return {"limit": limit, "remaining": limit, "reset": window}


class DistributedRateLimitMiddleware(BaseHTTPMiddleware):
    """Distributed rate limiting middleware using Redis"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.rate_limiter = RedisRateLimiter()
        
        # Configuration
        self.rate_limit_requests = 100  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.block_duration = 300  # seconds (5 minutes)
        
        # Per-endpoint limits
        self.endpoint_limits = {
            "/api/auth/login": {"limit": 5, "window": 60},
            "/api/auth/register": {"limit": 3, "window": 300},
            "/api/chat/message": {"limit": 30, "window": 60},
        }
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch"""
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/api/health", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check endpoint-specific limits
        endpoint_config = self.endpoint_limits.get(request.url.path)
        if endpoint_config:
            limit = endpoint_config["limit"]
            window = endpoint_config["window"]
        else:
            limit = self.rate_limit_requests
            window = self.rate_limit_window
        
        # Check rate limit
        is_allowed, rate_info = self.rate_limiter.check_rate_limit(
            key=client_id,
            limit=limit,
            window=window,
            block_duration=self.block_duration if not endpoint_config else None
        )
        
        if not is_allowed:
            log_security_event(logger, "rate_limit_exceeded", 
                             ip_address=client_id,
                             details=rate_info)
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": rate_info["limit"],
                    "remaining": rate_info["remaining"],
                    "reset_in": rate_info["reset"]
                }
            )
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
            response.headers["Retry-After"] = str(rate_info["reset"])
            
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        rate_info = self.rate_limiter.get_rate_limit_info(client_id, limit, window)
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get user ID from token if authenticated
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                import jwt
                from utils.config import AppConfig
                token = auth_header.replace("Bearer ", "")
                payload = jwt.decode(token, AppConfig.JWT_SECRET_KEY, 
                                    algorithms=[AppConfig.JWT_ALGORITHM],
                                    options={"verify_exp": False})
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except Exception:
                pass
        
        # Fallback to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
