"""
Configuration management for AWS Chatbot
Centralized configuration with proper validation and security
"""

import os
from typing import Optional, Any, Dict
from decouple import config, Csv
from pathlib import Path
import logging
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration management with validation"""
    
    def __init__(self):
        self.config_cache: Dict[str, Any] = {}
        self._encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_path = Path(".encryption_key")
        
        if key_path.exists():
            with open(key_path, "rb") as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_path, "wb") as f:
                f.write(key)
            logger.info("Generated new encryption key")
            return key
    
    def get(self, key: str, default: Any = None, cast: type = str, required: bool = False) -> Any:
        """Get configuration value with caching and validation"""
        if key in self.config_cache:
            return self.config_cache[key]
        
        try:
            value = config(key, default=default, cast=cast)
            
            if required and (value is None or value == ""):
                raise ValueError(f"Required configuration key '{key}' is missing or empty")
            
            # Cache the value
            self.config_cache[key] = value
            return value
            
        except Exception as e:
            if required:
                logger.error(f"Failed to get required config key '{key}': {e}")
                raise
            else:
                logger.warning(f"Failed to get config key '{key}', using default: {e}")
                return default
    
    def get_list(self, key: str, default: list = None, separator: str = ",") -> list:
        """Get configuration value as list"""
        if default is None:
            default = []
        
        try:
            return config(key, default=default, cast=Csv())
        except Exception as e:
            logger.warning(f"Failed to get list config '{key}': {e}")
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get configuration value as boolean"""
        return self.get(key, default=default, cast=bool)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get configuration value as integer"""
        return self.get(key, default=default, cast=int)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get configuration value as float"""
        return self.get(key, default=default, cast=float)
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt sensitive configuration value"""
        try:
            encrypted = self.fernet.encrypt(value.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt value: {e}")
            raise
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration value"""
        try:
            decoded = base64.b64decode(encrypted_value.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            raise
    
    def validate_required_configs(self) -> bool:
        """Validate all required configuration values"""
        required_configs = [
            ("JWT_SECRET_KEY", str),
            ("DATABASE_URL", str),
            ("AWS_DEFAULT_REGION", str),
        ]
        
        missing_configs = []
        
        for config_key, config_type in required_configs:
            try:
                self.get(config_key, required=True, cast=config_type)
            except ValueError:
                missing_configs.append(config_key)
        
        if missing_configs:
            logger.error(f"Missing required configurations: {missing_configs}")
            return False
        
        logger.info("All required configurations validated successfully")
        return True

# Global configuration instance
cfg = ConfigManager()

# Application Configuration
class AppConfig:
    """Application configuration with validation"""
    
    # Basic App Settings
    APP_NAME = cfg.get("APP_NAME", default="AWS Chatbot")
    APP_VERSION = cfg.get("APP_VERSION", default="1.0.0")
    ENVIRONMENT = cfg.get("NODE_ENV", default="development")
    DEBUG = cfg.get_bool("DEBUG", default=True)
    
    # Server Configuration
    HOST = cfg.get("HOST", default="0.0.0.0")
    PORT = cfg.get_int("PORT", default=8000)
    
    # Database Configuration
    DATABASE_URL = cfg.get("DATABASE_URL", required=True)
    
    # JWT Configuration
    JWT_SECRET_KEY = cfg.get("JWT_SECRET_KEY", required=True)
    JWT_ALGORITHM = cfg.get("JWT_ALGORITHM", default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = cfg.get_int("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", default=30)
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES = cfg.get_int("JWT_REFRESH_TOKEN_EXPIRE_MINUTES", default=10080)
    
    # Security Configuration
    SECRET_KEY = cfg.get("SECRET_KEY", required=True)
    BCRYPT_ROUNDS = cfg.get_int("BCRYPT_ROUNDS", default=12)
    
    # CORS Configuration
    CORS_ORIGINS = cfg.get_list("CORS_ORIGINS", default=["http://localhost:3000"])
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = cfg.get("GOOGLE_CLIENT_ID", default="")
    GOOGLE_CLIENT_SECRET = cfg.get("GOOGLE_CLIENT_SECRET", default="")
    PROTON_CLIENT_ID = cfg.get("PROTON_CLIENT_ID", default="")
    PROTON_CLIENT_SECRET = cfg.get("PROTON_CLIENT_SECRET", default="")
    GOOGLE_REDIRECT_URI = cfg.get("GOOGLE_REDIRECT_URI", default="http://localhost:3000/auth/google/callback")
    PROTON_REDIRECT_URI = cfg.get("PROTON_REDIRECT_URI", default="http://localhost:3000/auth/proton/callback")
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = cfg.get("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = cfg.get("AWS_SECRET_ACCESS_KEY", default="")
    AWS_DEFAULT_REGION = cfg.get("AWS_DEFAULT_REGION", default="us-east-1")
    AWS_SESSION_TOKEN = cfg.get("AWS_SESSION_TOKEN", default="")
    AWS_CREDENTIALS_TIMEOUT = cfg.get_int("AWS_CREDENTIALS_TIMEOUT", default=30)
    AWS_MAX_RETRIES = cfg.get_int("AWS_MAX_RETRIES", default=3)
    AWS_BOTO3_SESSION_CACHE_TTL = cfg.get_int("AWS_BOTO3_SESSION_CACHE_TTL", default=3600)
    # Common defaults for AWS resources (can be overridden per environment)
    DEFAULT_EC2_AMI = cfg.get("DEFAULT_EC2_AMI", default="ami-0c02fb55956c7d316")
    
    # Email Configuration
    SMTP_SERVER = cfg.get("SMTP_SERVER", default="smtp.gmail.com")
    SMTP_PORT = cfg.get_int("SMTP_PORT", default=587)
    SMTP_USE_TLS = cfg.get_bool("SMTP_USE_TLS", default=True)
    SMTP_USERNAME = cfg.get("SMTP_USERNAME", default="")
    SMTP_PASSWORD = cfg.get("SMTP_PASSWORD", default="")
    FROM_EMAIL = cfg.get("FROM_EMAIL", default="")
    
    # Redis Configuration
    REDIS_URL = cfg.get("REDIS_URL", default="redis://localhost:6379/0")
    
    # Logging Configuration
    LOG_LEVEL = cfg.get("LOG_LEVEL", default="INFO")
    LOG_FORMAT = cfg.get("LOG_FORMAT", default="console")
    
    # Security Settings
    RATE_LIMIT_REQUESTS = cfg.get_int("RATE_LIMIT_REQUESTS", default=100)
    RATE_LIMIT_WINDOW = cfg.get_int("RATE_LIMIT_WINDOW", default=60)
    MAX_REQUEST_SIZE = cfg.get_int("MAX_REQUEST_SIZE", default=10485760)  # 10MB
    
    @classmethod
    def validate(cls) -> bool:
        """Validate all configuration values"""
        return cfg.validate_required_configs()
    
    @classmethod
    def get_aws_credentials(cls) -> tuple[str, str, str]:
        """Get AWS credentials (decrypted if necessary)"""
        return (
            cls.AWS_ACCESS_KEY_ID,
            cls.AWS_SECRET_ACCESS_KEY,
            cls.AWS_SESSION_TOKEN
        )
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() in ["production", "prod"]
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT.lower() in ["development", "dev"]
    
    @classmethod
    def get_database_config(cls) -> dict:
        """Get database configuration"""
        return {
            "url": cls.DATABASE_URL,
            "echo": cls.DEBUG and cls.is_development(),
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }
    
    @classmethod
    def get_email_config(cls) -> dict:
        """Get email configuration"""
        return {
            "smtp_server": cls.SMTP_SERVER,
            "smtp_port": cls.SMTP_PORT,
            "use_tls": cls.SMTP_USE_TLS,
            "username": cls.SMTP_USERNAME,
            "password": cls.SMTP_PASSWORD,
            "from_email": cls.FROM_EMAIL,
        }

class SecurityConfig:
    """Security-specific configuration"""
    
    # TLS/HTTPS Configuration
    TLS_ENABLED = cfg.get_bool("TLS_ENABLED", default=False)
    TLS_CERT_PATH = cfg.get("TLS_CERT_PATH", default="/etc/ssl/certs/cert.pem")
    TLS_KEY_PATH = cfg.get("TLS_KEY_PATH", default="/etc/ssl/private/key.pem")
    
    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }
    
    # Content Security Policy
    CSP_POLICY = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' https://accounts.google.com https://oauth2.googleapis.com;"
    )
    
    # Rate Limiting
    RATE_LIMIT_STORAGE = cfg.get("RATE_LIMIT_STORAGE", default="memory")  # memory, redis
    
    # IP Whitelist
    IP_WHITELIST = cfg.get_list("IP_WHITELIST", default=["127.0.0.1", "::1"])
    
    @classmethod
    def get_security_headers(cls) -> dict:
        """Get security headers with CSP"""
        headers = cls.SECURITY_HEADERS.copy()
        headers["Content-Security-Policy"] = cls.CSP_POLICY
        return headers

def validate_configuration():
    """Validate all configuration on startup"""
    logger.info("Validating configuration...")
    
    if not AppConfig.validate():
        raise RuntimeError("Configuration validation failed")
    
    # Check AWS credentials if provided
    if AppConfig.AWS_ACCESS_KEY_ID and AppConfig.AWS_SECRET_ACCESS_KEY:
        logger.info("AWS credentials configured")
    else:
        logger.warning("AWS credentials not configured - some features may not work")
    
    # Check OAuth configuration
    oauth_providers = []
    if AppConfig.GOOGLE_CLIENT_ID and AppConfig.GOOGLE_CLIENT_SECRET:
        oauth_providers.append("Google")
    if AppConfig.PROTON_CLIENT_ID and AppConfig.PROTON_CLIENT_SECRET:
        oauth_providers.append("Proton")
    
    if oauth_providers:
        logger.info(f"OAuth providers configured: {', '.join(oauth_providers)}")
    else:
        logger.warning("No OAuth providers configured")
    
    logger.info("Configuration validation completed successfully")

# Export commonly used configurations
__all__ = [
    "AppConfig",
    "SecurityConfig", 
    "cfg",
    "validate_configuration"
]
