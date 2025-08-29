"""
Encryption utilities for AWS Chatbot
Secure encryption/decryption for sensitive data like AWS credentials
"""

import os
import base64
import hashlib
import time
import ipaddress
from typing import Tuple, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets
import logging

from utils.config import AppConfig

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption and decryption of sensitive data"""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption manager with master key"""
        self.master_key = master_key or AppConfig.SECRET_KEY
        self._encryption_keys = {}
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _get_encryption_key(self, key_id: str = "default") -> Fernet:
        """Get or create encryption key for specific purpose"""
        if key_id not in self._encryption_keys:
            # Use master key + key_id to create unique encryption key
            salt = hashlib.sha256(f"{self.master_key}{key_id}".encode()).digest()[:16]
            derived_key = self._derive_key(self.master_key, salt)
            self._encryption_keys[key_id] = Fernet(derived_key)
        
        return self._encryption_keys[key_id]
    
    def encrypt(self, data: str, key_id: str = "default") -> str:
        """Encrypt string data and return base64 encoded result"""
        try:
            fernet = self._get_encryption_key(key_id)
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str, key_id: str = "default") -> str:
        """Decrypt base64 encoded data and return original string"""
        try:
            fernet = self._get_encryption_key(key_id)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_aws_credentials(self, access_key: str, secret_key: str, session_token: str = "") -> Tuple[str, str, str]:
        """Encrypt AWS credentials for secure storage"""
        try:
            encrypted_access = self.encrypt(access_key, "aws_access")
            encrypted_secret = self.encrypt(secret_key, "aws_secret")
            encrypted_session = self.encrypt(session_token, "aws_session") if session_token else ""
            
            logger.info("AWS credentials encrypted successfully")
            return encrypted_access, encrypted_secret, encrypted_session
        except Exception as e:
            logger.error(f"Failed to encrypt AWS credentials: {e}")
            raise
    
    def decrypt_aws_credentials(self, encrypted_access: str, encrypted_secret: str, encrypted_session: str = "") -> Tuple[str, str, str]:
        """Decrypt AWS credentials for use"""
        try:
            access_key = self.decrypt(encrypted_access, "aws_access")
            secret_key = self.decrypt(encrypted_secret, "aws_secret")
            session_token = self.decrypt(encrypted_session, "aws_session") if encrypted_session else ""
            
            logger.debug("AWS credentials decrypted successfully")
            return access_key, secret_key, session_token
        except Exception as e:
            logger.error(f"Failed to decrypt AWS credentials: {e}")
            raise
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Hash password with salt for secure storage"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        hashed = kdf.derive(password.encode())
        
        return (
            base64.urlsafe_b64encode(hashed).decode(),
            base64.urlsafe_b64encode(salt).decode()
        )
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against stored hash and salt"""
        try:
            salt_bytes = base64.urlsafe_b64decode(salt.encode())
            stored_hash = base64.urlsafe_b64decode(hashed_password.encode())
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
                backend=default_backend()
            )
            
            # This will raise an exception if passwords don't match
            kdf.verify(password.encode(), stored_hash)
            return True
        except Exception:
            return False

class SecureStorage:
    """Secure storage utilities for sensitive data"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
    
    def store_user_aws_credentials(self, user_id: int, access_key: str, secret_key: str, session_token: str = "") -> dict:
        """Store encrypted AWS credentials for user"""
        try:
            encrypted_access, encrypted_secret, encrypted_session = self.encryption_manager.encrypt_aws_credentials(
                access_key, secret_key, session_token
            )
            
            return {
                "user_id": user_id,
                "encrypted_aws_access_key": encrypted_access,
                "encrypted_aws_secret_key": encrypted_secret,
                "encrypted_aws_session_token": encrypted_session,
                "encryption_version": "v1"
            }
        except Exception as e:
            logger.error(f"Failed to store AWS credentials for user {user_id}: {e}")
            raise
    
    def retrieve_user_aws_credentials(self, encrypted_data: dict) -> Tuple[str, str, str]:
        """Retrieve and decrypt AWS credentials for user"""
        try:
            access_key, secret_key, session_token = self.encryption_manager.decrypt_aws_credentials(
                encrypted_data["encrypted_aws_access_key"],
                encrypted_data["encrypted_aws_secret_key"],
                encrypted_data.get("encrypted_aws_session_token", "")
            )
            
            return access_key, secret_key, session_token
        except Exception as e:
            logger.error(f"Failed to retrieve AWS credentials: {e}")
            raise
    
    def generate_api_key(self, user_id: int, purpose: str = "api") -> str:
        """Generate secure API key for user"""
        timestamp = str(int(time.time()))
        data = f"{user_id}:{purpose}:{timestamp}"
        token = self.encryption_manager.generate_secure_token()
        
        # Create API key with embedded metadata
        api_key_data = f"{data}:{token}"
        encrypted_api_key = self.encryption_manager.encrypt(api_key_data, "api_keys")
        
        return f"awsbot_{encrypted_api_key}"
    
    def validate_api_key(self, api_key: str) -> Optional[dict]:
        """Validate and extract information from API key"""
        try:
            if not api_key.startswith("awsbot_"):
                return None
            
            encrypted_data = api_key[7:]  # Remove "awsbot_" prefix
            decrypted_data = self.encryption_manager.decrypt(encrypted_data, "api_keys")
            
            parts = decrypted_data.split(":")
            if len(parts) != 4:
                return None
            
            user_id, purpose, timestamp, token = parts
            
            return {
                "user_id": int(user_id),
                "purpose": purpose,
                "timestamp": int(timestamp),
                "token": token
            }
        except Exception as e:
            logger.warning(f"Invalid API key: {e}")
            return None

# TLS/SSL Configuration utilities
class TLSManager:
    """Manages TLS/SSL certificates and configuration"""
    
    @staticmethod
    def generate_self_signed_cert(cert_path: str, key_path: str, hostname: str = "localhost"):
        """Generate self-signed certificate for development"""
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime
            
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AWS Chatbot"),
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(hostname),
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Write certificate and key
            os.makedirs(os.path.dirname(cert_path), exist_ok=True)
            os.makedirs(os.path.dirname(key_path), exist_ok=True)
            
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            with open(key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            logger.info(f"Self-signed certificate generated: {cert_path}")
            return True
            
        except ImportError:
            logger.error("cryptography package required for certificate generation")
            return False
        except Exception as e:
            logger.error(f"Failed to generate certificate: {e}")
            return False
    
    @staticmethod
    def validate_certificate(cert_path: str, key_path: str) -> bool:
        """Validate certificate and key files"""
        try:
            return os.path.exists(cert_path) and os.path.exists(key_path)
        except Exception as e:
            logger.error(f"Certificate validation failed: {e}")
            return False

# Global instances
encryption_manager = EncryptionManager()
secure_storage = SecureStorage(encryption_manager)
tls_manager = TLSManager()

# Export utilities
__all__ = [
    "EncryptionManager",
    "SecureStorage",
    "TLSManager",
    "encryption_manager",
    "secure_storage",
    "tls_manager"
]
