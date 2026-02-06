"""
AWS S3 Service Implementation
S3 bucket and object management functionality
"""

import boto3
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from datetime import datetime
from utils.logger import get_aws_logger
from .aws_client import AWSBaseClient
from database import AWSResource

logger = get_aws_logger()


class S3Service(AWSBaseClient):
    """S3 service implementation for bucket and object management"""
    
    def __init__(self, db: Session, user_id: int):
        super().__init__(db, user_id, "s3")
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def list_buckets(self) -> Dict[str, Any]:
        """List all S3 buckets"""
        try:
            response = self.client.list_buckets()
            
            buckets = []
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                # Get bucket location and additional info
                try:
                    location_response = self.client.get_bucket_location(Bucket=bucket_name)
                    region = location_response.get('LocationConstraint') or 'us-east-1'
                except:
                    region = self.get_user_region()
                
                # Get bucket size and object count (approximate)
                try:
                    paginator = self.client.get_paginator('list_objects_v2')
                    total_size = 0
                    object_count = 0
                    for page in paginator.paginate(Bucket=bucket_name):
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                total_size += obj.get('Size', 0)
                                object_count += 1
                except:
                    total_size = 0
                    object_count = 0
                
                bucket_data = {
                    "bucket_name": bucket_name,
                    "creation_date": bucket['CreationDate'].isoformat() if bucket.get('CreationDate') else None,
                    "region": region,
                    "object_count": object_count,
                    "total_size": total_size,
                    "total_size_gb": round(total_size / (1024**3), 2)
                }
                buckets.append(bucket_data)
                
                # Track in database
                self._track_aws_resource(
                    resource_type='s3',
                    resource_id=bucket_name,
                    resource_name=bucket_name,
                    resource_arn=f"arn:aws:s3:::{bucket_name}",
                    status='active',
                    meta_data=bucket_data
                )
            
            result = {
                "success": True,
                "buckets": buckets,
                "count": len(buckets),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("list_buckets", {"count": len(buckets)})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_buckets")
    
    def create_bucket(self, bucket_name: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Create a new S3 bucket"""
        try:
            bucket_region = region or self.get_user_region()
            
            # Create bucket configuration
            if bucket_region == 'us-east-1':
                # us-east-1 doesn't require LocationConstraint
                self.client.create_bucket(Bucket=bucket_name)
            else:
                self.client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': bucket_region}
                )
            
            # Track in database
            self._track_aws_resource(
                resource_type='s3',
                resource_id=bucket_name,
                resource_name=bucket_name,
                resource_arn=f"arn:aws:s3:::{bucket_name}",
                status='active',
                meta_data={'region': bucket_region},
                created_via_chat=True
            )
            
            result = {
                "success": True,
                "bucket_name": bucket_name,
                "region": bucket_region,
                "message": f"Bucket '{bucket_name}' created successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("create_bucket", {"bucket_name": bucket_name, "region": bucket_region})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "create_bucket", {"bucket_name": bucket_name})
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> Dict[str, Any]:
        """Delete an S3 bucket"""
        try:
            if force:
                # Delete all objects first
                paginator = self.client.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=bucket_name):
                    if 'Contents' in page:
                        objects = [{'Key': obj['Key']} for obj in page['Contents']]
                        if objects:
                            self.client.delete_objects(
                                Bucket=bucket_name,
                                Delete={'Objects': objects}
                            )
            
            self.client.delete_bucket(Bucket=bucket_name)
            
            result = {
                "success": True,
                "bucket_name": bucket_name,
                "message": f"Bucket '{bucket_name}' deleted successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("delete_bucket", {"bucket_name": bucket_name})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "delete_bucket", {"bucket_name": bucket_name})
    
    def list_objects(self, bucket_name: str, prefix: Optional[str] = None) -> Dict[str, Any]:
        """List objects in an S3 bucket"""
        try:
            params = {'Bucket': bucket_name}
            if prefix:
                params['Prefix'] = prefix
            
            paginator = self.client.get_paginator('list_objects_v2')
            objects = []
            
            for page in paginator.paginate(**params):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        objects.append({
                            "key": obj['Key'],
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat(),
                            "storage_class": obj.get('StorageClass', 'STANDARD'),
                            "etag": obj.get('ETag', '').strip('"')
                        })
            
            result = {
                "success": True,
                "bucket_name": bucket_name,
                "objects": objects,
                "count": len(objects),
                "prefix": prefix,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_objects", {"bucket_name": bucket_name})
