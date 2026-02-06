"""
AWS Base Client
Provides common AWS client functionality and session management
"""

import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy.orm import Session
from datetime import datetime

from .credential_manager import AWSCredentialManager
from utils.logger import get_aws_logger
from database import User, SystemLog, AWSResource

logger = get_aws_logger()

class AWSBaseClient:
    """Base class for all AWS service clients"""
    
    def __init__(self, db: Session, user_id: int, service_name: str):
        """
        Initialize AWS client for a specific user and service
        
        Args:
            db: Database session
            user_id: User ID
            service_name: AWS service name (e.g., 'ec2', 's3', 'lambda')
        """
        self.db = db
        self.user_id = user_id
        self.service_name = service_name
        self.credential_manager = AWSCredentialManager()
        self.session = None
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the AWS client with user credentials"""
        try:
            # Get user credentials
            credentials = self.credential_manager.get_credentials(self.db, self.user_id)
            
            if not credentials:
                raise ValueError(f"No AWS credentials found for user {self.user_id}")
            
            # Create AWS session
            self.session = boto3.Session(**credentials)
            
            # Create service client
            self.client = self.session.client(self.service_name)
            
            logger.info(f"AWS {self.service_name} client initialized for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS {self.service_name} client for user {self.user_id}: {e}")
            self._log_error("client_initialization_failed", str(e))
            raise
    
    def _log_operation(self, operation: str, details: Dict[str, Any], 
                      level: str = "info", status: str = "success"):
        """
        Log AWS operations to the database
        
        Args:
            operation: Operation name
            details: Operation details
            level: Log level
            status: Operation status
        """
        try:
            log_entry = SystemLog(
                user_id=self.user_id,
                level=level,
                service=f"aws_{self.service_name}",
                operation=operation,
                message=f"AWS {self.service_name} operation: {operation}",
                meta_data={
                    "details": details,
                    "status": status,
                    "service": self.service_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log AWS operation: {e}")
    
    def _log_error(self, operation: str, error_message: str, details: Optional[Dict[str, Any]] = None):
        """Log AWS operation errors"""
        self._log_operation(
            operation=operation,
            details=details or {"error": error_message},
            level="error",
            status="failed"
        )
    
    def _handle_aws_error(self, error: Exception, operation: str, 
                         details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle AWS API errors and return standardized error response
        
        Args:
            error: The exception that occurred
            operation: The operation that failed
            details: Additional operation details
            
        Returns:
            Standardized error response
        """
        error_response = {
            "success": False,
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if isinstance(error, ClientError):
            error_code = error.response['Error']['Code']
            error_message = error.response['Error']['Message']
            
            error_response.update({
                "error_code": error_code,
                "error_message": error_message,
                "error_type": "AWS_CLIENT_ERROR"
            })
            
            logger.error(f"AWS {self.service_name} ClientError in {operation}: {error_code} - {error_message}")
            
        elif isinstance(error, NoCredentialsError):
            error_response.update({
                "error_code": "NO_CREDENTIALS",
                "error_message": "AWS credentials not found or invalid",
                "error_type": "CREDENTIALS_ERROR"
            })
            
            logger.error(f"AWS {self.service_name} NoCredentialsError in {operation}")
            
        else:
            error_response.update({
                "error_code": "UNKNOWN_ERROR",
                "error_message": str(error),
                "error_type": "UNEXPECTED_ERROR"
            })
            
            logger.error(f"Unexpected error in AWS {self.service_name} {operation}: {error}")
        
        # Log the error
        self._log_error(operation, error_response["error_message"], details)
        
        return error_response
    
    def get_user_region(self) -> str:
        """Get the user's configured AWS region"""
        try:
            user = self.db.query(User).filter(User.id == self.user_id).first()
            return user.aws_region if user and user.aws_region else 'us-east-1'
        except Exception as e:
            logger.error(f"Failed to get user region: {e}")
            return 'us-east-1'
    
    def change_region(self, region: str) -> bool:
        """
        Change the AWS region for this client
        
        Args:
            region: New AWS region
            
        Returns:
            bool: Success status
        """
        try:
            # Update client with new region
            credentials = self.credential_manager.get_credentials(self.db, self.user_id)
            if not credentials:
                return False
            
            credentials['region_name'] = region
            self.session = boto3.Session(**credentials)
            self.client = self.session.client(self.service_name)
            
            # Update user's default region in database
            user = self.db.query(User).filter(User.id == self.user_id).first()
            if user:
                user.aws_region = region
                user.updated_at = datetime.utcnow()
                self.db.commit()
            
            logger.info(f"Changed AWS region to {region} for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change AWS region for user {self.user_id}: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the AWS connection and return status
        
        Returns:
            Connection status information
        """
        try:
            if not self.client:
                return {
                    "success": False,
                    "error": "Client not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Try a simple operation to test connection
            if self.service_name == 'sts':
                response = self.client.get_caller_identity()
                return {
                    "success": True,
                    "account_id": response.get('Account'),
                    "user_id": response.get('UserId'),
                    "arn": response.get('Arn'),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                # For other services, we'll implement specific test methods
                return {
                    "success": True,
                    "message": f"AWS {self.service_name} client is ready",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return self._handle_aws_error(e, "test_connection")
    
    def get_service_quotas(self) -> Dict[str, Any]:
        """
        Get service quotas and limits (where applicable)
        
        Returns:
            Service quota information
        """
        try:
            # This is a placeholder - implementation varies by service
            return {
                "success": True,
                "service": self.service_name,
                "quotas": {},
                "message": "Service quotas not implemented for this service yet",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return self._handle_aws_error(e, "get_service_quotas")
    
    def _track_aws_resource(self, resource_type: str, resource_id: str, 
                           resource_name: str, resource_arn: str, 
                           status: str, meta_data: Dict[str, Any],
                           created_via_chat: bool = False):
        """Track AWS resource in database"""
        try:
            # Check if resource already exists
            existing_resource = self.db.query(AWSResource).filter(
                AWSResource.user_id == self.user_id,
                AWSResource.resource_id == resource_id
            ).first()
            
            if existing_resource:
                # Update existing resource
                existing_resource.status = status
                existing_resource.meta_data = meta_data
                existing_resource.updated_at = datetime.utcnow()
            else:
                # Create new resource tracking
                new_resource = AWSResource(
                    user_id=self.user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    resource_arn=resource_arn,
                    region=self.get_user_region(),
                    status=status,
                    meta_data=meta_data,
                    created_via_chat=created_via_chat
                )
                self.db.add(new_resource)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to track AWS resource: {e}")
            self.db.rollback()
