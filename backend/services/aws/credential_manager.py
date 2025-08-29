"""
AWS Credentials Manager
Handles secure storage, encryption, and validation of AWS credentials
"""

import boto3
import json
from typing import Dict, Optional, Tuple, Any
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import User
from utils.encryption import EncryptionManager
from utils.logger import get_aws_logger
from utils.config import AppConfig

logger = get_aws_logger()

class AWSCredentialManager:
    """Manages AWS credentials for users with encryption and validation"""
    
    def __init__(self):
        self.cipher = EncryptionManager()
        self.default_region = AppConfig.AWS_DEFAULT_REGION
    
    def store_credentials(self, db: Session, user_id: int, 
                         access_key: str, secret_key: str, 
                         region: Optional[str] = None) -> bool:
        """
        Store encrypted AWS credentials for a user
        
        Args:
            db: Database session
            user_id: User ID
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            region: AWS region (optional)
            
        Returns:
            bool: Success status
        """
        try:
            # Validate credentials before storing
            is_valid, validation_info = self.validate_credentials(access_key, secret_key, region)
            
            if not is_valid:
                logger.error(f"Invalid AWS credentials provided for user {user_id}: {validation_info}")
                return False
            
            # Encrypt credentials
            encrypted_access_key = self.cipher.encrypt(access_key, "aws_access")
            encrypted_secret_key = self.cipher.encrypt(secret_key, "aws_secret")
            
            # Update user record
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            user.aws_access_key = encrypted_access_key
            user.aws_secret_key = encrypted_secret_key
            user.aws_region = region or self.default_region
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"AWS credentials stored successfully for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store AWS credentials for user {user_id}: {e}")
            db.rollback()
            return False
    
    def get_credentials(self, db: Session, user_id: int) -> Optional[Dict[str, str]]:
        """
        Retrieve and decrypt AWS credentials for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dict containing AWS credentials or None if not found
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.aws_access_key or not user.aws_secret_key:
                logger.warning(f"No AWS credentials found for user {user_id}")
                return None
            
            # Decrypt credentials
            access_key = self.cipher.decrypt(user.aws_access_key, "aws_access")
            secret_key = self.cipher.decrypt(user.aws_secret_key, "aws_secret")
            
            return {
                'aws_access_key_id': access_key,
                'aws_secret_access_key': secret_key,
                'region_name': user.aws_region or self.default_region
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve AWS credentials for user {user_id}: {e}")
            return None
    
    def validate_credentials(self, access_key: str, secret_key: str, 
                           region: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate AWS credentials by making a test API call
        
        Args:
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            region: AWS region
            
        Returns:
            Tuple of (is_valid, validation_info)
        """
        try:
            # Create a test session
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region or self.default_region
            )
            
            # Test with STS to get caller identity (minimal permissions required)
            sts_client = session.client('sts')
            response = sts_client.get_caller_identity()
            
            validation_info = {
                'account_id': response.get('Account'),
                'user_id': response.get('UserId'),
                'arn': response.get('Arn'),
                'region': region or self.default_region,
                'validated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"AWS credentials validated successfully for account {response.get('Account')}")
            return True, validation_info
            
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            error_info = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'validated_at': datetime.utcnow().isoformat()
            }
            logger.warning(f"AWS credentials validation failed: {error_info}")
            return False, error_info
            
        except Exception as e:
            error_info = {
                'error_type': 'UnexpectedError',
                'error_message': str(e),
                'validated_at': datetime.utcnow().isoformat()
            }
            logger.error(f"Unexpected error during AWS credentials validation: {error_info}")
            return False, error_info
    
    def test_permissions(self, db: Session, user_id: int, 
                        service: str = 'ec2') -> Dict[str, Any]:
        """
        Test AWS permissions for specific services
        
        Args:
            db: Database session
            user_id: User ID
            service: AWS service to test (default: ec2)
            
        Returns:
            Dict containing permission test results
        """
        try:
            credentials = self.get_credentials(db, user_id)
            if not credentials:
                return {
                    'success': False,
                    'error': 'No AWS credentials found',
                    'permissions': {}
                }
            
            session = boto3.Session(**credentials)
            results = {'success': True, 'permissions': {}, 'tested_at': datetime.utcnow().isoformat()}
            
            if service == 'ec2':
                # Test EC2 permissions
                ec2_client = session.client('ec2')
                
                # Test describe instances (read permission)
                try:
                    ec2_client.describe_instances(MaxResults=5)
                    results['permissions']['ec2:DescribeInstances'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeInstances'] = False
                    results['permissions']['ec2:DescribeInstances_error'] = str(e)
                
                # Test describe images (AMI access)
                try:
                    ec2_client.describe_images(Owners=['self'], MaxResults=5)
                    results['permissions']['ec2:DescribeImages'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeImages'] = False
                    results['permissions']['ec2:DescribeImages_error'] = str(e)
                
                # Test describe security groups
                try:
                    ec2_client.describe_security_groups(MaxResults=5)
                    results['permissions']['ec2:DescribeSecurityGroups'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeSecurityGroups'] = False
                    results['permissions']['ec2:DescribeSecurityGroups_error'] = str(e)
                
                # Test describe key pairs
                try:
                    ec2_client.describe_key_pairs()
                    results['permissions']['ec2:DescribeKeyPairs'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeKeyPairs'] = False
                    results['permissions']['ec2:DescribeKeyPairs_error'] = str(e)
            
            logger.info(f"AWS permissions tested for user {user_id}, service {service}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to test AWS permissions for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'permissions': {},
                'tested_at': datetime.utcnow().isoformat()
            }
    
    def remove_credentials(self, db: Session, user_id: int) -> bool:
        """
        Remove AWS credentials for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            bool: Success status
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return False
            
            user.aws_access_key = None
            user.aws_secret_key = None
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"AWS credentials removed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove AWS credentials for user {user_id}: {e}")
            db.rollback()
            return False
    
    def get_available_regions(self) -> Dict[str, str]:
        """
        Get list of available AWS regions
        
        Returns:
            Dict mapping region codes to region names
        """
        try:
            # Create a default session to get regions
            ec2 = boto3.client('ec2', region_name=self.default_region)
            response = ec2.describe_regions()
            
            regions = {}
            for region in response['Regions']:
                region_code = region['RegionName']
                # Map some common regions to friendly names
                friendly_names = {
                    'us-east-1': 'US East (N. Virginia)',
                    'us-west-2': 'US West (Oregon)', 
                    'us-west-1': 'US West (N. California)',
                    'eu-west-1': 'Europe (Ireland)',
                    'eu-central-1': 'Europe (Frankfurt)',
                    'ap-southeast-1': 'Asia Pacific (Singapore)',
                    'ap-northeast-1': 'Asia Pacific (Tokyo)',
                    'ap-south-1': 'Asia Pacific (Mumbai)',
                }
                
                regions[region_code] = friendly_names.get(region_code, region_code)
            
            return regions
            
        except Exception as e:
            logger.error(f"Failed to get AWS regions: {e}")
            # Return some default regions if API call fails
            return {
                'us-east-1': 'US East (N. Virginia)',
                'us-west-2': 'US West (Oregon)',
                'eu-west-1': 'Europe (Ireland)',
                'ap-southeast-1': 'Asia Pacific (Singapore)',
            }
    
    def test_service_permissions(self, access_key: str, secret_key: str, 
                               region: str, service: str = 'ec2') -> Dict[str, Any]:
        """
        Test AWS permissions for specific services using provided credentials
        
        Args:
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            region: AWS region
            service: AWS service to test (default: ec2)
            
        Returns:
            Dict containing permission test results
        """
        try:
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            results = {'success': True, 'permissions': {}, 'tested_at': datetime.utcnow().isoformat()}
            
            if service == 'ec2':
                # Test EC2 permissions
                ec2_client = session.client('ec2')
                
                # Test describe instances (read permission)
                try:
                    ec2_client.describe_instances(MaxResults=5)
                    results['permissions']['ec2:DescribeInstances'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeInstances'] = False
                    results['permissions']['ec2:DescribeInstances_error'] = str(e)
                
                # Test describe images (AMI access)
                try:
                    ec2_client.describe_images(Owners=['amazon'], MaxResults=5)
                    results['permissions']['ec2:DescribeImages'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeImages'] = False
                    results['permissions']['ec2:DescribeImages_error'] = str(e)
                
                # Test describe security groups
                try:
                    ec2_client.describe_security_groups(MaxResults=5)
                    results['permissions']['ec2:DescribeSecurityGroups'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeSecurityGroups'] = False
                    results['permissions']['ec2:DescribeSecurityGroups_error'] = str(e)
                
                # Test describe key pairs
                try:
                    ec2_client.describe_key_pairs()
                    results['permissions']['ec2:DescribeKeyPairs'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeKeyPairs'] = False
                    results['permissions']['ec2:DescribeKeyPairs_error'] = str(e)
                
                # Test run instances permission (check if we can launch)
                try:
                    # Just validate we can call the API, don't actually launch
                    ec2_client.describe_instance_types(MaxResults=5)
                    results['permissions']['ec2:DescribeInstanceTypes'] = True
                except ClientError as e:
                    results['permissions']['ec2:DescribeInstanceTypes'] = False
                    results['permissions']['ec2:DescribeInstanceTypes_error'] = str(e)
            
            logger.info(f"AWS permissions tested for service {service}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to test AWS permissions: {e}")
            return {
                'success': False,
                'error': str(e),
                'permissions': {},
                'tested_at': datetime.utcnow().isoformat()
            }
