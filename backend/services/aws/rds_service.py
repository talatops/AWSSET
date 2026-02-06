"""
AWS RDS Service Implementation
RDS database instance management functionality
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


class RDSService(AWSBaseClient):
    """RDS service implementation for database instance management"""
    
    def __init__(self, db: Session, user_id: int):
        super().__init__(db, user_id, "rds")
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def list_db_instances(self) -> Dict[str, Any]:
        """List all RDS database instances"""
        try:
            response = self.client.describe_db_instances()
            
            instances = []
            for db_instance in response.get('DBInstances', []):
                instance_data = {
                    "db_instance_identifier": db_instance['DBInstanceIdentifier'],
                    "db_instance_class": db_instance['DBInstanceClass'],
                    "engine": db_instance['Engine'],
                    "engine_version": db_instance.get('EngineVersion', ''),
                    "status": db_instance['DBInstanceStatus'],
                    "master_username": db_instance.get('MasterUsername', ''),
                    "db_name": db_instance.get('DBName', ''),
                    "allocated_storage": db_instance.get('AllocatedStorage', 0),
                    "storage_type": db_instance.get('StorageType', ''),
                    "endpoint": db_instance.get('Endpoint', {}).get('Address', ''),
                    "port": db_instance.get('Endpoint', {}).get('Port', 0),
                    "availability_zone": db_instance.get('AvailabilityZone', ''),
                    "multi_az": db_instance.get('MultiAZ', False),
                    "publicly_accessible": db_instance.get('PubliclyAccessible', False),
                    "backup_retention_period": db_instance.get('BackupRetentionPeriod', 0),
                    "created_time": db_instance.get('InstanceCreateTime', '').isoformat() if db_instance.get('InstanceCreateTime') else None
                }
                instances.append(instance_data)
                
                # Track in database
                self._track_aws_resource(
                    resource_type='rds',
                    resource_id=db_instance['DBInstanceIdentifier'],
                    resource_name=db_instance['DBInstanceIdentifier'],
                    resource_arn=db_instance.get('DBInstanceArn', ''),
                    status=db_instance['DBInstanceStatus'],
                    meta_data=instance_data
                )
            
            result = {
                "success": True,
                "instances": instances,
                "count": len(instances),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("list_db_instances", {"count": len(instances)})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_db_instances")
    
    def get_db_instance(self, db_instance_identifier: str) -> Dict[str, Any]:
        """Get detailed information about an RDS instance"""
        try:
            response = self.client.describe_db_instances(
                DBInstanceIdentifier=db_instance_identifier
            )
            
            if not response.get('DBInstances'):
                return {
                    "success": False,
                    "error": "Database instance not found",
                    "db_instance_identifier": db_instance_identifier
                }
            
            db_instance = response['DBInstances'][0]
            instance_data = {
                "db_instance_identifier": db_instance['DBInstanceIdentifier'],
                "db_instance_class": db_instance['DBInstanceClass'],
                "engine": db_instance['Engine'],
                "engine_version": db_instance.get('EngineVersion', ''),
                "status": db_instance['DBInstanceStatus'],
                "master_username": db_instance.get('MasterUsername', ''),
                "db_name": db_instance.get('DBName', ''),
                "allocated_storage": db_instance.get('AllocatedStorage', 0),
                "storage_type": db_instance.get('StorageType', ''),
                "endpoint": db_instance.get('Endpoint', {}).get('Address', ''),
                "port": db_instance.get('Endpoint', {}).get('Port', 0),
                "availability_zone": db_instance.get('AvailabilityZone', ''),
                "multi_az": db_instance.get('MultiAZ', False),
                "publicly_accessible": db_instance.get('PubliclyAccessible', False),
                "backup_retention_period": db_instance.get('BackupRetentionPeriod', 0),
                "vpc_security_groups": [sg['VpcSecurityGroupId'] for sg in db_instance.get('VpcSecurityGroups', [])],
                "db_subnet_group": db_instance.get('DBSubnetGroup', {}).get('DBSubnetGroupName', ''),
                "created_time": db_instance.get('InstanceCreateTime', '').isoformat() if db_instance.get('InstanceCreateTime') else None
            }
            
            result = {
                "success": True,
                "instance": instance_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "get_db_instance", {"db_instance_identifier": db_instance_identifier})
    
    def create_db_instance(self, db_instance_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new RDS database instance"""
        try:
            required_params = ['DBInstanceIdentifier', 'DBInstanceClass', 'Engine', 'MasterUsername', 'MasterUserPassword']
            for param in required_params:
                if param not in db_instance_config:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "required_params": required_params
                    }
            
            create_params = {
                'DBInstanceIdentifier': db_instance_config['DBInstanceIdentifier'],
                'DBInstanceClass': db_instance_config['DBInstanceClass'],
                'Engine': db_instance_config['Engine'],
                'MasterUsername': db_instance_config['MasterUsername'],
                'MasterUserPassword': db_instance_config['MasterUserPassword'],
                'AllocatedStorage': db_instance_config.get('AllocatedStorage', 20),
                'StorageType': db_instance_config.get('StorageType', 'gp2')
            }
            
            # Optional parameters
            if 'DBName' in db_instance_config:
                create_params['DBName'] = db_instance_config['DBName']
            if 'EngineVersion' in db_instance_config:
                create_params['EngineVersion'] = db_instance_config['EngineVersion']
            if 'VpcSecurityGroupIds' in db_instance_config:
                create_params['VpcSecurityGroupIds'] = db_instance_config['VpcSecurityGroupIds']
            if 'DBSubnetGroupName' in db_instance_config:
                create_params['DBSubnetGroupName'] = db_instance_config['DBSubnetGroupName']
            if 'PubliclyAccessible' in db_instance_config:
                create_params['PubliclyAccessible'] = db_instance_config['PubliclyAccessible']
            if 'BackupRetentionPeriod' in db_instance_config:
                create_params['BackupRetentionPeriod'] = db_instance_config['BackupRetentionPeriod']
            
            response = self.client.create_db_instance(**create_params)
            
            db_instance = response['DBInstance']
            
            # Track in database
            self._track_aws_resource(
                resource_type='rds',
                resource_id=db_instance['DBInstanceIdentifier'],
                resource_name=db_instance['DBInstanceIdentifier'],
                resource_arn=db_instance.get('DBInstanceArn', ''),
                status=db_instance['DBInstanceStatus'],
                meta_data={'engine': db_instance['Engine'], 'class': db_instance['DBInstanceClass']},
                created_via_chat=True
            )
            
            result = {
                "success": True,
                "db_instance_identifier": db_instance['DBInstanceIdentifier'],
                "status": db_instance['DBInstanceStatus'],
                "message": f"RDS instance '{db_instance['DBInstanceIdentifier']}' creation initiated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("create_db_instance", {"db_instance_identifier": db_instance['DBInstanceIdentifier']})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "create_db_instance", db_instance_config)
    
    def delete_db_instance(self, db_instance_identifier: str, 
                          skip_final_snapshot: bool = True,
                          final_snapshot_identifier: Optional[str] = None) -> Dict[str, Any]:
        """Delete an RDS database instance"""
        try:
            delete_params = {
                'DBInstanceIdentifier': db_instance_identifier,
                'SkipFinalSnapshot': skip_final_snapshot
            }
            
            if not skip_final_snapshot and final_snapshot_identifier:
                delete_params['FinalDBSnapshotIdentifier'] = final_snapshot_identifier
            
            self.client.delete_db_instance(**delete_params)
            
            result = {
                "success": True,
                "db_instance_identifier": db_instance_identifier,
                "message": f"RDS instance '{db_instance_identifier}' deletion initiated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("delete_db_instance", {"db_instance_identifier": db_instance_identifier})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "delete_db_instance", {"db_instance_identifier": db_instance_identifier})
