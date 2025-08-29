"""
Security middleware for AWS Chatbot
Rate limiting, CORS, security headers, and request validation
"""

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import hashlib
from collections import defaultdict, deque
from typing import Dict, Optional
import ipaddress
from datetime import datetime, timedelta
import json

from utils.logger import get_security_logger, log_security_event

logger = get_security_logger()

class SecurityMiddleware(BaseHTTPMiddleware):
    """Custom security middleware for enhanced protection"""
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        
        # Rate limiting storage
        self.rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque())
        self.blocked_ips: Dict[str, datetime] = {}
        
        # Configuration
        self.rate_limit_requests = 100  # requests per minute
        self.rate_limit_window = 60  # seconds
        self.block_duration = 300  # seconds (5 minutes)
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        
        # Suspicious patterns
        self.suspicious_patterns = [
            "select ", "union ", "drop ", "delete ", "insert ",
            "<script", "javascript:", "eval(", "alert(",
            "../", "..\\", "/etc/passwd", "/proc/",
            "cmd.exe", "powershell", "bash", "sh ",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch"""
        start_time = time.time()
        
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Check if IP is blocked
            if self._is_ip_blocked(client_ip):
                log_security_event(logger, "blocked_ip_attempt", ip_address=client_ip)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "IP temporarily blocked due to suspicious activity"}
                )
            
            # Rate limiting
            if not self._check_rate_limit(client_ip):
                self._block_ip(client_ip)
                log_security_event(logger, "rate_limit_exceeded", ip_address=client_ip)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
            
            # Request size validation
            if hasattr(request, 'headers') and 'content-length' in request.headers:
                content_length = int(request.headers.get('content-length', 0))
                if content_length > self.max_request_size:
                    log_security_event(logger, "oversized_request", ip_address=client_ip, 
                                     details={"size": content_length})
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Request too large"}
                    )
            
            # Content validation
            await self._validate_request_content(request, client_ip)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            # Log request
            process_time = time.time() - start_time
            self._log_request(request, response, client_ip, process_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip in self.blocked_ips:
            if datetime.utcnow() > self.blocked_ips[ip]:
                # Unblock expired IPs
                del self.blocked_ips[ip]
                return False
            return True
        return False
    
    def _block_ip(self, ip: str):
        """Block IP for specified duration"""
        self.blocked_ips[ip] = datetime.utcnow() + timedelta(seconds=self.block_duration)
        logger.warning(f"IP {ip} blocked for {self.block_duration} seconds")
    
    def _check_rate_limit(self, ip: str) -> bool:
        """Check rate limiting for IP"""
        now = time.time()
        window_start = now - self.rate_limit_window
        
        # Clean old requests
        while self.rate_limit_storage[ip] and self.rate_limit_storage[ip][0] < window_start:
            self.rate_limit_storage[ip].popleft()
        
        # Check if under limit
        if len(self.rate_limit_storage[ip]) >= self.rate_limit_requests:
            return False
        
        # Add current request
        self.rate_limit_storage[ip].append(now)
        return True
    
    async def _validate_request_content(self, request: Request, client_ip: str):
        """Validate request content for suspicious patterns"""
        # Check URL path
        path = str(request.url.path).lower()
        query = str(request.url.query).lower()
        
        for pattern in self.suspicious_patterns:
            if pattern in path or pattern in query:
                log_security_event(logger, "suspicious_pattern_detected", 
                                 ip_address=client_ip,
                                 details={"pattern": pattern, "path": path, "query": query})
                # Don't block immediately, just log for monitoring
                break
        
        # Skip request body validation to avoid consuming the request stream
        # Request body validation can be done at the application level if needed
        # The body can only be read once in FastAPI, and we need to preserve it for the endpoint handlers
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://accounts.google.com https://oauth2.googleapis.com;",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
    
    def _log_request(self, request: Request, response: Response, client_ip: str, process_time: float):
        """Log request details"""
        request_data = {
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "status_code": response.status_code,
            "process_time": round(process_time, 3),
            "ip_address": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer")
        }
        
        if response.status_code >= 400:
            logger.warning("HTTP error response", extra=request_data)
        else:
            logger.info("HTTP request processed", extra=request_data)

class IPWhitelist:
    """IP whitelist management"""
    
    def __init__(self):
        self.whitelist = [
            "127.0.0.1",
            "::1",
            "localhost",
            # Add your development IPs here
        ]
    
    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for whitelisted in self.whitelist:
                try:
                    if ip_obj == ipaddress.ip_address(whitelisted):
                        return True
                except ValueError:
                    # Handle hostnames
                    if ip == whitelisted:
                        return True
            return False
        except ValueError:
            return False

class RequestValidator:
    """Additional request validation utilities"""
    
    @staticmethod
    def validate_json_size(data: dict, max_depth: int = 10, max_keys: int = 1000) -> bool:
        """Validate JSON structure to prevent DoS attacks"""
        def count_items(obj, depth=0):
            if depth > max_depth:
                return float('inf')
            
            if isinstance(obj, dict):
                count = len(obj)
                for value in obj.values():
                    count += count_items(value, depth + 1)
                return count
            elif isinstance(obj, list):
                count = len(obj)
                for item in obj:
                    count += count_items(item, depth + 1)
                return count
            return 1
        
        return count_items(data) <= max_keys
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """Basic input sanitization"""
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            input_string = input_string.replace(char, '')
        return input_string.strip()

# Rate limiting decorator for specific endpoints
def rate_limit(requests_per_minute: int = 60):
    """Decorator for endpoint-specific rate limiting"""
    def decorator(func):
        func._rate_limit = requests_per_minute
        return func
    return decorator
