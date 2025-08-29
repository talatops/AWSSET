import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError, NoCredentialsError
from utils.logger import get_aws_logger

logger = get_aws_logger()

class AWSStatsService:
    """Service for fetching AWS account statistics and metrics"""
    
    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        self.credentials = credentials
        self.region = credentials.get('region_name', 'us-east-1') if credentials else 'us-east-1'
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        if credentials:
            self.session = boto3.Session(**credentials)
    
    def _get_client(self, service_name: str):
        """Get a client for the specified service"""
        if not self.session:
            raise ValueError("No AWS session available")
        return self.session.client(service_name)
    
    async def get_all_service_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for all AWS services
        """
        try:
            # Run all service stats in parallel for better performance
            tasks = [
                self._get_ec2_stats(),
                self._get_s3_stats(),
                self._get_lambda_stats(),
                self._get_rds_stats(),
                self._get_iam_stats(),
                self._get_bedrock_stats(),
                self._get_account_summary()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            ec2_stats, s3_stats, lambda_stats, rds_stats, iam_stats, bedrock_stats, account_summary = results
            
            # Handle any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    service_names = ['EC2', 'S3', 'Lambda', 'RDS', 'IAM', 'Bedrock', 'Account']
                    logger.error(f"Error fetching {service_names[i]} stats: {result}")
            
            return {
                'success': True,
                'timestamp': datetime.utcnow().isoformat(),
                'region': self.region,
                'account_summary': account_summary if not isinstance(account_summary, Exception) else {},
                'services': {
                    'ec2': ec2_stats if not isinstance(ec2_stats, Exception) else self._get_default_ec2_stats(),
                    's3': s3_stats if not isinstance(s3_stats, Exception) else self._get_default_s3_stats(),
                    'lambda': lambda_stats if not isinstance(lambda_stats, Exception) else self._get_default_lambda_stats(),
                    'rds': rds_stats if not isinstance(rds_stats, Exception) else self._get_default_rds_stats(),
                    'iam': iam_stats if not isinstance(iam_stats, Exception) else self._get_default_iam_stats(),
                    'bedrock': bedrock_stats if not isinstance(bedrock_stats, Exception) else self._get_default_bedrock_stats()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get AWS service stats: {e}")
            return self._get_default_stats()
    
    async def _get_ec2_stats(self) -> Dict[str, Any]:
        """Get EC2 service statistics"""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_ec2_data():
                ec2_client = self._get_client('ec2')
                
                # Get instances
                instances_response = ec2_client.describe_instances()
                instances = []
                for reservation in instances_response['Reservations']:
                    instances.extend(reservation['Instances'])
                
                # Count by state
                running = sum(1 for i in instances if i['State']['Name'] == 'running')
                stopped = sum(1 for i in instances if i['State']['Name'] == 'stopped')
                total = len(instances)
                
                # Get AMIs count (limit to avoid timeout)
                try:
                    amis_response = ec2_client.describe_images(Owners=['self'], MaxResults=100)
                    amis_count = len(amis_response['Images'])
                except:
                    amis_count = 0
                
                # Get Security Groups
                try:
                    sg_response = ec2_client.describe_security_groups()
                    security_groups = len(sg_response['SecurityGroups'])
                except:
                    security_groups = 0
                
                # Get Key Pairs
                try:
                    kp_response = ec2_client.describe_key_pairs()
                    key_pairs = len(kp_response['KeyPairs'])
                except:
                    key_pairs = 0
                
                return {
                    'status': 'active' if total > 0 else 'inactive',
                    'instances': total,
                    'running': running,
                    'stopped': stopped,
                    'amis': amis_count,
                    'security_groups': security_groups,
                    'key_pairs': key_pairs,
                    'cost': 'N/A'  # Would need Cost Explorer API for real costs
                }
            
            return await loop.run_in_executor(self.executor, fetch_ec2_data)
            
        except Exception as e:
            logger.error(f"Error fetching EC2 stats: {e}")
            raise
    
    async def _get_s3_stats(self) -> Dict[str, Any]:
        """Get S3 service statistics"""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_s3_data():
                s3_client = self._get_client('s3')
                
                # Get buckets
                try:
                    buckets_response = s3_client.list_buckets()
                    buckets_count = len(buckets_response['Buckets'])
                    
                    # Get total objects and size (for first few buckets to avoid timeout)
                    total_objects = 0
                    total_size = 0
                    
                    for bucket in buckets_response['Buckets'][:5]:  # Limit to first 5 buckets
                        try:
                            bucket_name = bucket['Name']
                            objects_response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)
                            total_objects += objects_response.get('KeyCount', 0)
                            
                            # Calculate size (simplified)
                            if 'Contents' in objects_response:
                                for obj in objects_response['Contents']:
                                    total_size += obj.get('Size', 0)
                                    
                        except Exception as e:
                            logger.warning(f"Error accessing bucket {bucket_name}: {e}")
                            continue
                    
                    # Format size
                    if total_size > 1024**3:  # GB
                        size_str = f"{total_size / (1024**3):.1f} GB"
                    elif total_size > 1024**2:  # MB
                        size_str = f"{total_size / (1024**2):.1f} MB"
                    else:
                        size_str = f"{total_size / 1024:.1f} KB"
                    
                    return {
                        'status': 'active' if buckets_count > 0 else 'inactive',
                        'buckets': buckets_count,
                        'objects': f"{total_objects:,}" if total_objects < 1000000 else f"{total_objects/1000000:.1f}M",
                        'storage': size_str,
                        'cost': 'N/A'
                    }
                    
                except Exception as e:
                    logger.error(f"Error fetching S3 data: {e}")
                    return self._get_default_s3_stats()
            
            return await loop.run_in_executor(self.executor, fetch_s3_data)
            
        except Exception as e:
            logger.error(f"Error fetching S3 stats: {e}")
            raise
    
    async def _get_lambda_stats(self) -> Dict[str, Any]:
        """Get Lambda service statistics"""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_lambda_data():
                lambda_client = self._get_client('lambda')
                
                try:
                    # Get functions
                    functions_response = lambda_client.list_functions(MaxItems=100)
                    functions_count = len(functions_response['Functions'])
                    
                    return {
                        'status': 'active' if functions_count > 0 else 'inactive',
                        'functions': functions_count,
                        'executions': 'N/A',  # Would need CloudWatch for metrics
                        'errors': 'N/A',
                        'cost': 'N/A'
                    }
                    
                except Exception as e:
                    logger.error(f"Error fetching Lambda data: {e}")
                    return self._get_default_lambda_stats()
            
            return await loop.run_in_executor(self.executor, fetch_lambda_data)
            
        except Exception as e:
            logger.error(f"Error fetching Lambda stats: {e}")
            raise
    
    async def _get_rds_stats(self) -> Dict[str, Any]:
        """Get RDS service statistics"""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_rds_data():
                rds_client = self._get_client('rds')
                
                try:
                    # Get DB instances
                    instances_response = rds_client.describe_db_instances()
                    instances_count = len(instances_response['DBInstances'])
                    
                    # Count by status
                    available = sum(1 for db in instances_response['DBInstances'] 
                                  if db['DBInstanceStatus'] == 'available')
                    
                    return {
                        'status': 'active' if instances_count > 0 else 'inactive',
                        'databases': instances_count,
                        'available': available,
                        'connections': 'N/A',  # Would need CloudWatch
                        'storage': 'N/A',
                        'cost': 'N/A'
                    }
                    
                except Exception as e:
                    logger.error(f"Error fetching RDS data: {e}")
                    return self._get_default_rds_stats()
            
            return await loop.run_in_executor(self.executor, fetch_rds_data)
            
        except Exception as e:
            logger.error(f"Error fetching RDS stats: {e}")
            raise
    
    async def _get_iam_stats(self) -> Dict[str, Any]:
        """Get IAM service statistics"""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_iam_data():
                iam_client = self._get_client('iam')
                
                try:
                    # Get users
                    users_response = iam_client.list_users(MaxItems=100)
                    users_count = len(users_response['Users'])
                    
                    # Get roles
                    roles_response = iam_client.list_roles(MaxItems=100)
                    roles_count = len(roles_response['Roles'])
                    
                    # Get policies
                    policies_response = iam_client.list_policies(Scope='Local', MaxItems=100)
                    policies_count = len(policies_response['Policies'])
                    
                    return {
                        'status': 'active',
                        'users': users_count,
                        'roles': roles_count,
                        'policies': policies_count,
                        'cost': '$0.00'  # IAM is free
                    }
                    
                except Exception as e:
                    logger.error(f"Error fetching IAM data: {e}")
                    return self._get_default_iam_stats()
            
            return await loop.run_in_executor(self.executor, fetch_iam_data)
            
        except Exception as e:
            logger.error(f"Error fetching IAM stats: {e}")
            raise
    
    async def _get_bedrock_stats(self) -> Dict[str, Any]:
        """Get Bedrock service statistics"""
        try:
            # Bedrock might not be available in all regions
            return {
                'status': 'inactive',
                'models': 0,
                'requests': 0,
                'tokens': 0,
                'cost': '$0.00'
            }
            
        except Exception as e:
            logger.error(f"Error fetching Bedrock stats: {e}")
            raise
    
    async def _get_account_summary(self) -> Dict[str, Any]:
        """Get overall account summary"""
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_account_data():
                try:
                    sts_client = self._get_client('sts')
                    identity = sts_client.get_caller_identity()
                    
                    return {
                        'account_id': identity.get('Account'),
                        'user_arn': identity.get('Arn'),
                        'region': self.region
                    }
                except Exception as e:
                    logger.error(f"Error fetching account summary: {e}")
                    return {}
            
            return await loop.run_in_executor(self.executor, fetch_account_data)
            
        except Exception as e:
            logger.error(f"Error fetching account summary: {e}")
            raise
    
    # Default fallback methods
    def _get_default_stats(self) -> Dict[str, Any]:
        """Return default stats when AWS calls fail"""
        return {
            'success': False,
            'error': 'Unable to fetch AWS statistics',
            'timestamp': datetime.utcnow().isoformat(),
            'region': self.region or 'us-east-1',
            'services': {
                'ec2': self._get_default_ec2_stats(),
                's3': self._get_default_s3_stats(),
                'lambda': self._get_default_lambda_stats(),
                'rds': self._get_default_rds_stats(),
                'iam': self._get_default_iam_stats(),
                'bedrock': self._get_default_bedrock_stats()
            }
        }
    
    def _get_default_ec2_stats(self):
        return {
            'status': 'inactive',
            'instances': 0,
            'running': 0,
            'stopped': 0,
            'cost': '$0.00'
        }
    
    def _get_default_s3_stats(self):
        return {
            'status': 'inactive',
            'buckets': 0,
            'objects': '0',
            'storage': '0 GB',
            'cost': '$0.00'
        }
    
    def _get_default_lambda_stats(self):
        return {
            'status': 'inactive',
            'functions': 0,
            'executions': '0',
            'errors': 0,
            'cost': '$0.00'
        }
    
    def _get_default_rds_stats(self):
        return {
            'status': 'inactive',
            'databases': 0,
            'connections': 0,
            'storage': '0 GB',
            'cost': '$0.00'
        }
    
    def _get_default_iam_stats(self):
        return {
            'status': 'active',
            'users': 0,
            'roles': 0,
            'policies': 0,
            'cost': '$0.00'
        }
    
    def _get_default_bedrock_stats(self):
        return {
            'status': 'inactive',
            'models': 0,
            'requests': 0,
            'tokens': 0,
            'cost': '$0.00'
        }
