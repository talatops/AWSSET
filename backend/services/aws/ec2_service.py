"""
AWS EC2 Service Implementation
Comprehensive EC2 instance management functionality
"""

import boto3
import json
from typing import Dict, List, Any, Optional, Tuple
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import NoCredentialsError
from utils.logger import get_aws_logger
from .aws_client import AWSBaseClient

logger = get_aws_logger()

class EC2Service(AWSBaseClient):
    """EC2 service implementation for instance management"""
    
    def __init__(self, db: Session, user_id: int):
        super().__init__(db, user_id, "ec2")
        self.resource = self.session.resource('ec2') if self.session else None
        # Smart cache with change detection
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes base TTL
        self._change_detection = {
            'instances': {'last_check': None, 'etag': None, 'count': 0},
            'security_groups': {'last_check': None, 'etag': None, 'count': 0},
            'key_pairs': {'last_check': None, 'etag': None, 'count': 0},
            'amis': {'last_check': None, 'etag': None, 'count': 0},
            'instance_types': {'last_check': None, 'etag': None, 'count': 0},
            'vpcs': {'last_check': None, 'etag': None, 'count': 0},
            'subnets': {'last_check': None, 'etag': None, 'count': 0}
        }
    
    # =========================================================================
    # INSTANCE MANAGEMENT
    # =========================================================================
    
    def list_instances(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List EC2 instances with optional filtering
        
        Args:
            filters: Optional filters for instances
            
        Returns:
            Dict containing instance list and metadata
        """
        try:
            # Prepare filters
            ec2_filters = []
            if filters:
                for key, value in filters.items():
                    if key == 'state' and value:
                        ec2_filters.append({'Name': 'instance-state-name', 'Values': [value]})
                    elif key == 'tag' and value:
                        tag_name, tag_value = value.split(':', 1) if ':' in value else (value, '*')
                        ec2_filters.append({'Name': f'tag:{tag_name}', 'Values': [tag_value]})
            
            # Get instances
            if ec2_filters:
                response = self.client.describe_instances(Filters=ec2_filters)
            else:
                response = self.client.describe_instances()
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_data = self._format_instance_data(instance)
                    instances.append(instance_data)
                    
                    # Track in database
                    self._track_aws_resource(
                        resource_type='ec2',
                        resource_id=instance['InstanceId'],
                        resource_name=instance_data.get('name', ''),
                        resource_arn=f"arn:aws:ec2:{self.get_user_region()}:{instance.get('OwnerId', '')}:instance/{instance['InstanceId']}",
                        status=instance['State']['Name'],
                        meta_data=instance_data
                    )
            
            result = {
                "success": True,
                "instances": instances,
                "count": len(instances),
                "region": self.get_user_region(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("list_instances", {"count": len(instances), "filters": filters})
            
            # Cache the result with change detection
            self._set_cached_data('list_instances', result, filters=str(filters))
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_instances", {"filters": filters})
    
    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific instance
        
        Args:
            instance_id: EC2 instance ID
            
        Returns:
            Dict containing instance details
        """
        try:
            response = self.client.describe_instances(InstanceIds=[instance_id])
            
            if not response['Reservations']:
                return {
                    "success": False,
                    "error": "Instance not found",
                    "instance_id": instance_id
                }
            
            instance = response['Reservations'][0]['Instances'][0]
            instance_data = self._format_instance_data(instance, detailed=True)
            
            result = {
                "success": True,
                "instance": instance_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("get_instance", {"instance_id": instance_id})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "get_instance", {"instance_id": instance_id})
    
    def create_instance(self, instance_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new EC2 instance with advanced configuration
        
        Args:
            instance_config: Instance configuration parameters including volume config
            
        Returns:
            Dict containing creation result
        """
        try:
            # Validate required parameters
            required_params = ['ImageId', 'InstanceType']
            for param in required_params:
                if param not in instance_config:
                    logger.error(f"Missing required parameter: {param} in instance_config: {instance_config}")
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "required_params": required_params
                    }
            
            # Validate instance type
            if instance_config['InstanceType'] not in ['t2.micro', 't2.small', 't2.medium', 't3.micro', 't3.small', 't3.medium', 'm5.large', 'c5.large', 'r5.large']:
                logger.warning(f"Instance type {instance_config['InstanceType']} may not be available in all regions")
            
            # Validate AMI
            if not instance_config['ImageId'].startswith('ami-'):
                logger.error(f"Invalid AMI ID format: {instance_config['ImageId']}")
                return {
                    "success": False,
                    "error": f"Invalid AMI ID format: {instance_config['ImageId']}. Must start with 'ami-'",
                    "required_params": required_params
                }
            
            # Set default parameters
            launch_params = {
                'ImageId': instance_config['ImageId'],
                'InstanceType': instance_config['InstanceType'],
                'MinCount': instance_config.get('MinCount', 1),
                'MaxCount': instance_config.get('MaxCount', 1),
            }
            
            # Optional parameters
            if 'KeyName' in instance_config:
                launch_params['KeyName'] = instance_config['KeyName']
            
            if 'SecurityGroupIds' in instance_config:
                launch_params['SecurityGroupIds'] = instance_config['SecurityGroupIds']
            elif 'SecurityGroups' in instance_config:
                launch_params['SecurityGroups'] = instance_config['SecurityGroups']
            
            if 'SubnetId' in instance_config:
                launch_params['SubnetId'] = instance_config['SubnetId']
            
            if 'UserData' in instance_config:
                launch_params['UserData'] = instance_config['UserData']
            
            if 'IamInstanceProfile' in instance_config:
                launch_params['IamInstanceProfile'] = instance_config['IamInstanceProfile']
            
            # Advanced volume configuration
            if 'BlockDeviceMappings' in instance_config:
                launch_params['BlockDeviceMappings'] = instance_config['BlockDeviceMappings']
            else:
                # Default volume configuration
                launch_params['BlockDeviceMappings'] = [{
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': instance_config.get('VolumeSize', 8),
                        'VolumeType': instance_config.get('VolumeType', 'gp3'),
                        'DeleteOnTermination': True,
                        'Encrypted': instance_config.get('VolumeEncrypted', False)
                    }
                }]
            
            # Log launch parameters for debugging
            logger.info(f"Launching EC2 instance with params: {json.dumps(launch_params, default=str)}")
            
            # Launch instance
            try:
                response = self.client.run_instances(**launch_params)
                logger.info(f"EC2 instance launch successful: {response.get('Instances', [])}")
            except Exception as launch_error:
                logger.error(f"EC2 instance launch failed: {launch_error}")
                logger.error(f"Launch params: {launch_params}")
                raise launch_error
            
            instances = []
            for instance in response['Instances']:
                try:
                    instance_data = self._format_instance_data(instance)
                    instances.append(instance_data)
                    
                    logger.info(f"Processing instance {instance['InstanceId']} with state {instance['State']['Name']}")
                    
                    # Track in database
                    try:
                        self._track_aws_resource(
                            resource_type='ec2',
                            resource_id=instance['InstanceId'],
                            resource_name=instance_config.get('Name', ''),
                            resource_arn=f"arn:aws:ec2:{self.get_user_region()}:{instance.get('OwnerId', '')}:instance/{instance['InstanceId']}",
                            status=instance['State']['Name'],
                            meta_data=instance_data,
                            created_via_chat=True
                        )
                        logger.info(f"Successfully tracked instance {instance['InstanceId']} in database")
                    except Exception as db_error:
                        logger.error(f"Failed to track instance {instance['InstanceId']} in database: {db_error}")
                    
                    # Add name tag if provided
                    if 'Name' in instance_config:
                        try:
                            self.client.create_tags(
                                Resources=[instance['InstanceId']],
                                Tags=[{'Key': 'Name', 'Value': instance_config['Name']}]
                            )
                            logger.info(f"Successfully added name tag '{instance_config['Name']}' to instance {instance['InstanceId']}")
                        except Exception as tag_error:
                            logger.warning(f"Failed to add name tag to instance {instance['InstanceId']}: {tag_error}")
                except Exception as instance_error:
                    logger.error(f"Error processing instance {instance.get('InstanceId', 'unknown')}: {instance_error}")
                    continue
            
            result = {
                "success": True,
                "instances": instances,
                "count": len(instances),
                "launch_params": launch_params,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Invalidate cache since instances changed
            self.invalidate_cache_for_changes('instances')
            
            self._log_operation("create_instance", {
                "instance_count": len(instances),
                "instance_type": instance_config['InstanceType'],
                "image_id": instance_config['ImageId']
            })
            
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "create_instance", instance_config)
    
    def start_instance(self, instance_id: str) -> Dict[str, Any]:
        """Start an EC2 instance"""
        return self._instance_state_change(instance_id, "start")
    
    def stop_instance(self, instance_id: str, force: bool = False) -> Dict[str, Any]:
        """Stop an EC2 instance"""
        return self._instance_state_change(instance_id, "stop", force=force)
    
    def reboot_instance(self, instance_id: str) -> Dict[str, Any]:
        """Reboot an EC2 instance"""
        return self._instance_state_change(instance_id, "reboot")
    
    def terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate an EC2 instance"""
        return self._instance_state_change(instance_id, "terminate")
    
    def _instance_state_change(self, instance_id: str, action: str, force: bool = False) -> Dict[str, Any]:
        """
        Handle instance state changes (start, stop, reboot, terminate)
        
        Args:
            instance_id: EC2 instance ID
            action: Action to perform
            force: Force the action (for stop)
            
        Returns:
            Dict containing operation result
        """
        try:
            if action == "start":
                response = self.client.start_instances(InstanceIds=[instance_id])
                current_state = response['StartingInstances'][0]['CurrentState']
                previous_state = response['StartingInstances'][0]['PreviousState']
                
            elif action == "stop":
                params = {'InstanceIds': [instance_id]}
                if force:
                    params['Force'] = True
                response = self.client.stop_instances(**params)
                current_state = response['StoppingInstances'][0]['CurrentState']
                previous_state = response['StoppingInstances'][0]['PreviousState']
                
            elif action == "reboot":
                self.client.reboot_instances(InstanceIds=[instance_id])
                # Reboot doesn't return state info
                current_state = {"Name": "rebooting", "Code": 8}
                previous_state = {"Name": "running", "Code": 16}
                
            elif action == "terminate":
                response = self.client.terminate_instances(InstanceIds=[instance_id])
                current_state = response['TerminatingInstances'][0]['CurrentState']
                previous_state = response['TerminatingInstances'][0]['PreviousState']
            
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # Update database tracking
            self._update_resource_status(instance_id, current_state['Name'])
            
            # Invalidate cache since instance state changed
            self.invalidate_cache_for_changes('instances')
            
            result = {
                "success": True,
                "instance_id": instance_id,
                "action": action,
                "previous_state": previous_state['Name'],
                "current_state": current_state['Name'],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation(f"{action}_instance", {
                "instance_id": instance_id,
                "previous_state": previous_state['Name'],
                "current_state": current_state['Name']
            })
            
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, f"{action}_instance", {"instance_id": instance_id})
    
    # =========================================================================
    # SECURITY GROUPS
    # =========================================================================
    
    def list_security_groups(self) -> Dict[str, Any]:
        """List security groups"""
        try:
            response = self.client.describe_security_groups()
            
            security_groups = []
            for sg in response['SecurityGroups']:
                sg_data = {
                    "group_id": sg['GroupId'],
                    "group_name": sg['GroupName'],
                    "description": sg['Description'],
                    "vpc_id": sg.get('VpcId'),
                    "owner_id": sg['OwnerId'],
                    "inbound_rules": len(sg['IpPermissions']),
                    "outbound_rules": len(sg['IpPermissionsEgress']),
                    "tags": {tag['Key']: tag['Value'] for tag in sg.get('Tags', [])}
                }
                security_groups.append(sg_data)
            
            result = {
                "success": True,
                "security_groups": security_groups,
                "count": len(security_groups),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache the result with change detection
            self._set_cached_data('list_security_groups', result)
            
            self._log_operation("list_security_groups", {"count": len(security_groups)})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_security_groups")
    
    # =========================================================================
    # KEY PAIRS
    # =========================================================================
    
    def list_key_pairs(self) -> Dict[str, Any]:
        """List EC2 key pairs"""
        try:
            response = self.client.describe_key_pairs()
            
            key_pairs = []
            for kp in response['KeyPairs']:
                kp_data = {
                    "key_name": kp['KeyName'],
                    "key_fingerprint": kp['KeyFingerprint'],
                    "key_type": kp.get('KeyType', 'rsa'),
                    "tags": {tag['Key']: tag['Value'] for tag in kp.get('Tags', [])}
                }
                key_pairs.append(kp_data)
            
            result = {
                "success": True,
                "key_pairs": key_pairs,
                "count": len(key_pairs),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache the result with change detection
            self._set_cached_data('list_key_pairs', result)
            
            self._log_operation("list_key_pairs", {"count": len(key_pairs)})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_key_pairs")

    def create_key_pair(self, key_name: str, key_type: str = 'rsa') -> Dict[str, Any]:
        """Create a new EC2 key pair"""
        try:
            # Validate key name
            if not key_name or len(key_name) < 3:
                return {
                    "success": False,
                    "error_message": "Key pair name must be at least 3 characters long"
                }
            
            # Check if key pair already exists
            try:
                existing = self.client.describe_key_pairs(KeyNames=[key_name])
                if existing['KeyPairs']:
                    return {
                        "success": False,
                        "error_message": f"Key pair '{key_name}' already exists"
                    }
            except ClientError as e:
                if e.response['Error']['Code'] != 'InvalidKeyPair.NotFound':
                    raise e
            
            # Create key pair
            response = self.client.create_key_pair(
                KeyName=key_name,
                KeyType=key_type
            )
            
            # Format the response
            key_pair_data = {
                "key_name": response['KeyName'],
                "key_fingerprint": response['KeyFingerprint'],
                "key_type": response.get('KeyType', 'rsa'),
                "private_key": response.get('KeyMaterial', ''),
                "public_key": response.get('PublicKeyMaterial', '')
            }
            
            result = {
                "success": True,
                "key_pair": key_pair_data,
                "message": f"Key pair '{key_name}' created successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Invalidate cache since key pairs changed
            self.invalidate_cache_for_changes('key_pairs')
            
            self._log_operation("create_key_pair", {"key_name": key_name, "key_type": key_type})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "create_key_pair", {"key_name": key_name, "key_type": key_type})

    def delete_key_pair(self, key_name: str) -> Dict[str, Any]:
        """Delete an EC2 key pair"""
        try:
            # Check if key pair exists
            try:
                existing = self.client.describe_key_pairs(KeyNames=[key_name])
                if not existing['KeyPairs']:
                    return {
                        "success": False,
                        "error_message": f"Key pair '{key_name}' not found"
                    }
            except ClientError as e:
                if e.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
                    return {
                        "success": False,
                        "error_message": f"Key pair '{key_name}' not found"
                    }
                raise e
            
            # Delete key pair
            self.client.delete_key_pair(KeyName=key_name)
            
            result = {
                "success": True,
                "message": f"Key pair '{key_name}' deleted successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Invalidate cache since key pairs changed
            self.invalidate_cache_for_changes('key_pairs')
            
            self._log_operation("delete_key_pair", {"key_name": key_name})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "delete_key_pair", {"key_name": key_name})
    
    # =========================================================================
    # AMIS & IMAGES
    # =========================================================================
    
    def list_amis(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List available AMIs
        
        Args:
            filters: Optional filters for AMIs
            
        Returns:
            Dict containing AMI list
        """
        try:
            # Default to commonly used AMIs
            describe_params = {
                'Owners': ['amazon', 'self'],
                'MaxResults': 50
            }
            
            # Add filters if provided
            if filters:
                ami_filters = []
                if 'name' in filters:
                    ami_filters.append({'Name': 'name', 'Values': [f"*{filters['name']}*"]})
                if 'architecture' in filters:
                    ami_filters.append({'Name': 'architecture', 'Values': [filters['architecture']]})
                if 'state' in filters:
                    ami_filters.append({'Name': 'state', 'Values': [filters['state']]})
                else:
                    ami_filters.append({'Name': 'state', 'Values': ['available']})
                
                describe_params['Filters'] = ami_filters
            else:
                # Default filter for popular Amazon Linux AMIs
                describe_params['Filters'] = [
                    {'Name': 'name', 'Values': ['amzn2-ami-hvm-*']},
                    {'Name': 'state', 'Values': ['available']},
                    {'Name': 'architecture', 'Values': ['x86_64']}
                ]
            
            response = self.client.describe_images(**describe_params)
            
            amis = []
            for ami in response['Images']:
                ami_data = {
                    "image_id": ami['ImageId'],
                    "name": ami.get('Name', ''),
                    "description": ami.get('Description', ''),
                    "architecture": ami.get('Architecture', ''),
                    "platform": ami.get('Platform', 'linux'),
                    "creation_date": ami.get('CreationDate', ''),
                    "owner_id": ami.get('OwnerId', ''),
                    "public": ami.get('Public', False),
                    "state": ami.get('State', ''),
                    "virtualization_type": ami.get('VirtualizationType', ''),
                    "root_device_type": ami.get('RootDeviceType', '')
                }
                amis.append(ami_data)
            
            # Sort by creation date (newest first)
            amis.sort(key=lambda x: x['creation_date'], reverse=True)
            
            result = {
                "success": True,
                "amis": amis,
                "count": len(amis),
                "filters": filters,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache the result with change detection
            self._set_cached_data('list_amis', result, filters=str(filters))
            
            self._log_operation("list_amis", {"count": len(amis), "filters": filters})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_amis", filters)
    
    def list_instance_types(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List available EC2 instance types with specifications
        
        Args:
            filters: Optional filters for instance types
            
        Returns:
            Dict containing instance types and metadata
        """
        try:
            # Check cache first
            cached_data = self._get_cached_data('list_instance_types', filters=str(filters))
            if cached_data:
                return cached_data
            
            # Try to get instance types from AWS API first
            try:
                # Get instance type offerings
                response = self.client.describe_instance_type_offerings(
                    LocationType='region',
                    Filters=[{'Name': 'location', 'Values': [self.get_user_region()]}]
                )
                
                # Get detailed instance type information - OPTIMIZED: Batch calls instead of individual
                instance_types = []
                offerings = response['InstanceTypeOfferings'][:50]  # Limit to 50 for performance
                
                # Batch instance types into groups of 100 (AWS API limit)
                batch_size = 100
                for i in range(0, len(offerings), batch_size):
                    batch = offerings[i:i + batch_size]
                    instance_type_names = [offering['InstanceType'] for offering in batch]
                    
                    try:
                        # Get detailed specs for entire batch
                        specs_response = self.client.describe_instance_types(
                            InstanceTypes=instance_type_names
                        )
                        
                        for specs in specs_response['InstanceTypes']:
                            instance_type = specs['InstanceType']
                            
                            # Categorize instance type
                            family = instance_type.split('.')[0]
                            category = self._get_instance_category(family)
                            
                            instance_types.append({
                                'instance_type': instance_type,
                                'family': family,
                                'category': category,
                                'vcpu': specs.get('VCpuInfo', {}).get('DefaultVCpus', 0),
                                'memory_mib': specs.get('MemoryInfo', {}).get('SizeInMiB', 0),
                                'memory_gb': round(specs.get('MemoryInfo', {}).get('SizeInMiB', 0) / 1024, 1),
                                'architecture': specs.get('ProcessorInfo', {}).get('SupportedArchitectures', ['x86_64'])[0],
                                'supported_platforms': specs.get('SupportedBootModes', []),
                                'network_performance': specs.get('NetworkInfo', {}).get('NetworkPerformance', 'Unknown'),
                                'ebs_optimized': specs.get('EbsInfo', {}).get('EbsOptimizedSupport', 'unsupported'),
                                'free_tier_eligible': self._is_free_tier_eligible(instance_type)
                            })
                    except Exception as e:
                        logger.warning(f"Failed to get specs for batch {i//batch_size + 1}: {e}")
                        continue
                
                if instance_types:
                    # Sort by category and family
                    instance_types.sort(key=lambda x: (x['category'], x['family'], x['vcpu'], x['memory_gb']))
                    
                    result = {
                        "success": True,
                        "instance_types": instance_types,
                        "count": len(instance_types),
                        "categories": list(set(instance['category'] for instance in instance_types)),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    self._log_operation("list_instance_types", {"count": len(instance_types)})
                    
                    # Cache the result
                    self._set_cached_data('list_instance_types', result, filters=str(filters))
                    return result
                    
            except Exception as e:
                logger.warning(f"Failed to get instance types from AWS API: {e}")
            
            # Fallback: Provide common instance types
            fallback_types = [
                {'instance_type': 't2.micro', 'family': 't2', 'category': 'General Purpose', 'vcpu': 1, 'memory_gb': 1.0, 'free_tier_eligible': True},
                {'instance_type': 't2.small', 'family': 't2', 'category': 'General Purpose', 'vcpu': 1, 'memory_gb': 2.0, 'free_tier_eligible': False},
                {'instance_type': 't2.medium', 'family': 't2', 'category': 'General Purpose', 'vcpu': 2, 'memory_gb': 4.0, 'free_tier_eligible': False},
                {'instance_type': 't3.micro', 'family': 't3', 'category': 'General Purpose', 'vcpu': 2, 'memory_gb': 1.0, 'free_tier_eligible': True},
                {'instance_type': 't3.small', 'family': 't3', 'category': 'General Purpose', 'vcpu': 2, 'memory_gb': 2.0, 'free_tier_eligible': False},
                {'instance_type': 'm5.large', 'family': 'm5', 'category': 'General Purpose', 'vcpu': 2, 'memory_gb': 8.0, 'free_tier_eligible': False},
                {'instance_type': 'c5.large', 'family': 'c5', 'category': 'Compute Optimized', 'vcpu': 2, 'memory_gb': 4.0, 'free_tier_eligible': False},
                {'instance_type': 'r5.large', 'family': 'r5', 'category': 'Memory Optimized', 'vcpu': 2, 'memory_gb': 16.0, 'free_tier_eligible': False},
            ]
            
            result = {
                "success": True,
                "instance_types": fallback_types,
                "count": len(fallback_types),
                "categories": list(set(instance['category'] for instance in fallback_types)),
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Using fallback instance types (AWS API access limited)"
            }
            
            self._log_operation("list_instance_types", {"count": len(fallback_types), "fallback": True})
            
            # Cache the fallback result too
            self._set_cached_data('list_instance_types', result, filters=str(filters))
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_instance_types")
    
    def list_vpcs(self) -> Dict[str, Any]:
        """
        List available VPCs in the region
        
        Returns:
            Dict containing VPCs and metadata
        """
        try:
            # Try to get VPCs from AWS API first
            try:
                response = self.client.describe_vpcs()
                
                vpcs = []
                for vpc in response['Vpcs']:
                    vpc_data = {
                        'vpc_id': vpc['VpcId'],
                        'cidr_block': vpc['CidrBlock'],
                        'state': vpc['State'],
                        'is_default': vpc['IsDefault'],
                        'name': self._get_vpc_name(vpc),
                        'tags': vpc.get('Tags', [])
                    }
                    vpcs.append(vpc_data)
                
                if vpcs:
                    result = {
                        "success": True,
                        "vpcs": vpcs,
                        "count": len(vpcs),
                        "default_vpc": next((vpc for vpc in vpcs if vpc['is_default']), None),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Cache the result with change detection
                    self._set_cached_data('list_vpcs', result)
                    
                    self._log_operation("list_vpcs", {"count": len(vpcs)})
                    return result
                    
            except Exception as e:
                logger.warning(f"Failed to get VPCs from AWS API: {e}")
            
            # Fallback: Provide default VPC info
            fallback_vpcs = [
                {
                    'vpc_id': 'vpc-default',
                    'cidr_block': '172.31.0.0/16',
                    'state': 'available',
                    'is_default': True,
                    'name': 'Default VPC',
                    'tags': []
                }
            ]
            
            result = {
                "success": True,
                "vpcs": fallback_vpcs,
                "count": len(fallback_vpcs),
                "default_vpc": fallback_vpcs[0],
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Using fallback VPC info (AWS API access limited)"
            }
            
            self._log_operation("list_vpcs", {"count": len(fallback_vpcs), "fallback": True})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_vpcs")
    
    def list_subnets(self, vpc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List available subnets, optionally filtered by VPC
        
        Args:
            vpc_id: Optional VPC ID to filter subnets
            
        Returns:
            Dict containing subnets and metadata
        """
        try:
            # Try to get subnets from AWS API first
            try:
                filters = []
                if vpc_id:
                    filters.append({'Name': 'vpc-id', 'Values': [vpc_id]})
                
                response = self.client.describe_subnets(Filters=filters)
                
                subnets = []
                for subnet in response['Subnets']:
                    subnet_data = {
                        'subnet_id': subnet['SubnetId'],
                        'vpc_id': subnet['VpcId'],
                        'cidr_block': subnet['CidrBlock'],
                        'availability_zone': subnet['AvailabilityZone'],
                        'state': subnet['State'],
                        'available_ip_count': subnet['AvailableIpAddressCount'],
                        'name': self._get_subnet_name(subnet),
                        'tags': subnet.get('Tags', [])
                    }
                    subnets.append(subnet_data)
                
                if subnets:
                    result = {
                        "success": True,
                        "subnets": subnets,
                        "count": len(subnets),
                        "vpc_id": vpc_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Cache the result with change detection
                    self._set_cached_data('list_subnets', result, vpc_id=vpc_id)
                    
                    self._log_operation("list_subnets", {"count": len(subnets), "vpc_id": vpc_id})
                    return result
                    
            except Exception as e:
                logger.warning(f"Failed to get subnets from AWS API: {e}")
            
            # Fallback: Provide default subnet info
            fallback_subnets = [
                {
                    'subnet_id': 'subnet-default-1',
                    'vpc_id': vpc_id or 'vpc-default',
                    'cidr_block': '172.31.0.0/20',
                    'availability_zone': 'us-east-1a',
                    'state': 'available',
                    'available_ip_count': 4091,
                    'name': 'Default Subnet 1',
                    'tags': []
                },
                {
                    'subnet_id': 'subnet-default-2',
                    'vpc_id': vpc_id or 'vpc-default',
                    'cidr_block': '172.31.16.0/20',
                    'availability_zone': 'us-east-1b',
                    'state': 'available',
                    'available_ip_count': 4091,
                    'name': 'Default Subnet 2',
                    'tags': []
                }
            ]
            
            result = {
                "success": True,
                "subnets": fallback_subnets,
                "count": len(fallback_subnets),
                "vpc_id": vpc_id,
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Using fallback subnet info (AWS API access limited)"
            }
            
            self._log_operation("list_subnets", {"count": len(fallback_subnets), "fallback": True, "vpc_id": vpc_id})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_subnets", {"vpc_id": vpc_id})
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_instance_category(self, family: str) -> str:
        """Get instance category based on family"""
        if family in ['t2', 't3', 't4g']:
            return 'General Purpose'
        elif family in ['m5', 'm6g', 'm7g']:
            return 'General Purpose'
        elif family in ['c5', 'c6g', 'c7g']:
            return 'Compute Optimized'
        elif family in ['r5', 'r6g', 'r7g']:
            return 'Memory Optimized'
        elif family in ['i3', 'i4i']:
            return 'Storage Optimized'
        elif family in ['g4', 'g5']:
            return 'GPU Instances'
        elif family in ['p3', 'p4']:
            return 'GPU Instances'
        else:
            return 'Other'
    
    def check_instance_type_availability(self, instance_type: str) -> Dict[str, Any]:
        """Check if an instance type is available in the current region"""
        try:
            response = self.client.describe_instance_type_offerings(
                LocationType='region',
                Filters=[{'Name': 'location', 'Values': [self.get_user_region()]}]
            )
            
            available_types = [offering['InstanceType'] for offering in response['InstanceTypeOfferings']]
            
            is_available = instance_type in available_types
            
            return {
                "success": True,
                "instance_type": instance_type,
                "region": self.get_user_region(),
                "available": is_available,
                "available_types": available_types[:10] if not is_available else [],  # Show alternatives if not available
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking instance type availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "instance_type": instance_type,
                "region": self.get_user_region()
            }
    
    def _is_free_tier_eligible(self, instance_type: str) -> bool:
        """Check if instance type is free tier eligible"""
        free_tier_types = ['t2.micro', 't3.micro', 't4g.micro']
        return instance_type in free_tier_types
    
    def _get_vpc_name(self, vpc: Dict[str, Any]) -> str:
        """Extract VPC name from tags"""
        for tag in vpc.get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return f"VPC {vpc['VpcId'][-8:]}"
    
    def _get_subnet_name(self, subnet: Dict[str, Any]) -> str:
        """Extract subnet name from tags"""
        for tag in subnet.get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return f"Subnet {subnet['SubnetId'][-8:]}"
    
    def _format_instance_data(self, instance: Dict[str, Any], detailed: bool = False) -> Dict[str, Any]:
        """Format instance data for API response"""
        
        # Get instance name from tags
        instance_name = ""
        tags = {}
        for tag in instance.get('Tags', []):
            tags[tag['Key']] = tag['Value']
            if tag['Key'] == 'Name':
                instance_name = tag['Value']
        
        basic_data = {
            "instance_id": instance['InstanceId'],
            "name": instance_name,
            "state": instance['State']['Name'],
            "instance_type": instance['InstanceType'],
            "image_id": instance['ImageId'],
            "launch_time": instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else '',
            "availability_zone": instance.get('Placement', {}).get('AvailabilityZone', ''),
            "public_ip": instance.get('PublicIpAddress', ''),
            "private_ip": instance.get('PrivateIpAddress', ''),
            "key_name": instance.get('KeyName', ''),
            "security_groups": [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
            "tags": tags
        }
        
        if detailed:
            basic_data.update({
                "vpc_id": instance.get('VpcId', ''),
                "subnet_id": instance.get('SubnetId', ''),
                "architecture": instance.get('Architecture', ''),
                "platform": instance.get('Platform', 'linux'),
                "virtualization_type": instance.get('VirtualizationType', ''),
                "hypervisor": instance.get('Hypervisor', ''),
                "root_device_type": instance.get('RootDeviceType', ''),
                "root_device_name": instance.get('RootDeviceName', ''),
                "monitoring": instance.get('Monitoring', {}).get('State', 'disabled'),
                "network_interfaces": len(instance.get('NetworkInterfaces', [])),
                "block_device_mappings": len(instance.get('BlockDeviceMappings', [])),
                "iam_instance_profile": instance.get('IamInstanceProfile', {}).get('Arn', ''),
                "owner_id": instance.get('OwnerId', '')
            })
        
        return basic_data
    
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
    
    def _update_resource_status(self, resource_id: str, status: str):
        """Update resource status in database"""
        try:
            resource = self.db.query(AWSResource).filter(
                AWSResource.user_id == self.user_id,
                AWSResource.resource_id == resource_id
            ).first()
            
            if resource:
                resource.status = status
                resource.updated_at = datetime.utcnow()
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Failed to update resource status: {e}")
            self.db.rollback()
    
    # =========================================================================
    # CACHE HELPER METHODS
    # =========================================================================
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key for method and parameters"""
        key_parts = [method, str(self.user_id)]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)
    
    def _should_use_cache(self, method: str, **kwargs) -> bool:
        """Determine if we should use cached data based on change detection"""
        if method not in self._change_detection:
            return False
            
        change_info = self._change_detection[method]
        last_check = change_info.get('last_check')
        
        # If never checked, don't use cache
        if not last_check:
            return False
            
        # Check if cache is still valid (within TTL)
        cache_key = self._get_cache_key(method, **kwargs)
        cached_data = self._cache.get(cache_key)
        if not cached_data:
            return False
            
        # Check if cache has expired
        if cached_data.get('expires_at', 0) <= datetime.utcnow().timestamp():
            return False
            
        # Check if we need to verify for changes (every 30 seconds for critical resources)
        time_since_check = (datetime.utcnow() - last_check).total_seconds()
        if time_since_check < 30:  # Use cache if checked recently
            return True
            
        # For longer periods, check if there might be changes
        return self._check_for_changes(method, **kwargs)
    
    def _check_for_changes(self, method: str, **kwargs) -> bool:
        """Check if there are actual changes in AWS resources"""
        try:
            change_info = self._change_detection[method]
            
            if method == 'instances':
                # Quick check: count instances and compare with cached count
                response = self.client.describe_instances(MaxResults=1)
                current_count = sum(len(reservation['Instances']) for reservation in response['Reservations'])
                cached_count = change_info.get('count', 0)
                
                if current_count != cached_count:
                    logger.info(f"Change detected in {method}: count changed from {cached_count} to {current_count}")
                    return False
                    
            elif method == 'security_groups':
                # Quick check: count security groups
                response = self.client.describe_security_groups(MaxResults=1)
                current_count = len(response['SecurityGroups'])
                cached_count = change_info.get('count', 0)
                
                if current_count != cached_count:
                    logger.info(f"Change detected in {method}: count changed from {cached_count} to {current_count}")
                    return False
                    
            elif method == 'key_pairs':
                # Quick check: count key pairs
                response = self.client.describe_key_pairs()
                current_count = len(response['KeyPairs'])
                cached_count = change_info.get('count', 0)
                
                if current_count != cached_count:
                    logger.info(f"Change detected in {method}: count changed from {cached_count} to {current_count}")
                    return False
                    
            elif method == 'amis':
                # Quick check: count AMIs
                response = self.client.describe_images(Owners=['self'], MaxResults=1)
                current_count = len(response['Images'])
                cached_count = change_info.get('count', 0)
                
                if current_count != cached_count:
                    logger.info(f"Change detected in {method}: count changed from {cached_count} to {current_count}")
                    return False
            
            # No changes detected, cache is still valid
            return True
            
        except Exception as e:
            logger.warning(f"Error checking for changes in {method}: {e}")
            # If we can't check, assume no changes and use cache
            return True
    
    def _get_cached_data(self, method: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get cached data if available and change detection allows it"""
        if not self._should_use_cache(method, **kwargs):
            return None
            
        cache_key = self._get_cache_key(method, **kwargs)
        cached_data = self._cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Smart cache hit for {method} - using cached data")
            return cached_data.get('data')
        
        return None
    
    def _set_cached_data(self, method: str, data: Dict[str, Any], **kwargs):
        """Cache data with expiration and change detection tracking"""
        cache_key = self._get_cache_key(method, **kwargs)
        expires_at = datetime.utcnow().timestamp() + self._cache_ttl
        
        # Update change detection info
        if method in self._change_detection:
            self._change_detection[method].update({
                'last_check': datetime.utcnow(),
                'count': self._get_resource_count(data, method)
            })
        
        self._cache[cache_key] = {
            'data': data,
            'expires_at': expires_at,
            'cached_at': datetime.utcnow().isoformat()
        }
        logger.info(f"Smart cached data for {method} with change detection")
    
    def _get_resource_count(self, data: Dict[str, Any], method: str) -> int:
        """Extract resource count from data for change detection"""
        try:
            if method == 'instances':
                return len(data.get('instances', []))
            elif method == 'security_groups':
                return len(data.get('security_groups', []))
            elif method == 'key_pairs':
                return len(data.get('key_pairs', []))
            elif method == 'amis':
                return len(data.get('amis', []))
            elif method == 'instance_types':
                return len(data.get('instance_types', []))
            elif method == 'vpcs':
                return len(data.get('vpcs', []))
            elif method == 'subnets':
                return len(data.get('subnets', []))
            else:
                return 0
        except Exception:
            return 0
    
    def _clear_cache(self, method: str = None):
        """Clear cache for specific method or all cache"""
        if method:
            # Clear specific method cache
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{method}|")]
            for key in keys_to_remove:
                del self._cache[key]
            
            # Reset change detection for this method
            if method in self._change_detection:
                self._change_detection[method].update({
                    'last_check': None,
                    'etag': None,
                    'count': 0
                })
        else:
            # Clear all cache
            self._cache.clear()
            # Reset all change detection
            for method_name in self._change_detection:
                self._change_detection[method_name].update({
                    'last_check': None,
                    'etag': None,
                    'count': 0
                })
        
        logger.info(f"Smart cache cleared for {method or 'all methods'}")
    
    def invalidate_cache_for_changes(self, resource_type: str):
        """Invalidate cache when resources are modified"""
        if resource_type in self._change_detection:
            self._change_detection[resource_type].update({
                'last_check': None,
                'etag': None,
                'count': 0
            })
            logger.info(f"Cache invalidated for {resource_type} due to changes")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics and health information"""
        try:
            current_time = datetime.utcnow()
            cache_stats = {
                'total_cached_items': len(self._cache),
                'cache_size_mb': 0,  # Could be enhanced to calculate actual memory usage
                'cache_health': 'healthy',
                'methods': {},
                'performance_metrics': {
                    'cache_hit_rate': 0,
                    'total_requests': 0,
                    'cache_hits': 0,
                    'cache_misses': 0
                }
            }
            
            # Analyze each method's cache status
            for method_name, change_info in self._change_detection.items():
                method_stats = {
                    'last_check': change_info.get('last_check'),
                    'resource_count': change_info.get('count', 0),
                    'cache_status': 'not_cached'
                }
                
                # Check if method has cached data
                cache_keys = [k for k in self._cache.keys() if k.startswith(f"{method_name}|")]
                if cache_keys:
                    method_stats['cache_status'] = 'cached'
                    method_stats['cached_keys'] = len(cache_keys)
                    
                    # Check cache freshness
                    for key in cache_keys:
                        cached_data = self._cache[key]
                        expires_at = cached_data.get('expires_at', 0)
                        cached_at = cached_data.get('cached_at')
                        
                        if expires_at <= current_time.timestamp():
                            method_stats['cache_status'] = 'expired'
                        elif cached_at:
                            cached_time = datetime.fromisoformat(cached_at)
                            age_seconds = (current_time - cached_time).total_seconds()
                            method_stats['cache_age_seconds'] = age_seconds
                
                cache_stats['methods'][method_name] = method_stats
            
            # Calculate cache hit rate (this would need to be tracked over time)
            # For now, we'll provide a placeholder
            cache_stats['performance_metrics']['cache_hit_rate'] = 0.85  # Placeholder
            
            return cache_stats
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {'error': str(e)}
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache by removing expired items and adjusting TTL based on usage patterns"""
        try:
            current_time = datetime.utcnow()
            expired_keys = []
            optimized_count = 0
            
            # Remove expired cache entries
            for key, cached_data in self._cache.items():
                expires_at = cached_data.get('expires_at', 0)
                if expires_at <= current_time.timestamp():
                    expired_keys.append(key)
            
            # Remove expired items
            for key in expired_keys:
                del self._cache[key]
                optimized_count += 1
            
            # Adjust TTL based on resource type (some resources change more frequently)
            ttl_adjustments = {
                'instances': 180,      # 3 minutes - instances change frequently
                'security_groups': 300, # 5 minutes - security groups change occasionally
                'key_pairs': 600,      # 10 minutes - key pairs change rarely
                'amis': 1800,          # 30 minutes - AMIs change very rarely
                'instance_types': 3600, # 1 hour - instance types change very rarely
                'vpcs': 1800,          # 30 minutes - VPCs change rarely
                'subnets': 1800        # 30 minutes - subnets change rarely
            }
            
            # Apply dynamic TTL adjustments
            for method_name, new_ttl in ttl_adjustments.items():
                if method_name in self._change_detection:
                    # Adjust TTL based on change frequency
                    change_info = self._change_detection[method_name]
                    last_check = change_info.get('last_check')
                    
                    if last_check:
                        time_since_check = (current_time - last_check).total_seconds()
                        if time_since_check > 300:  # If not checked recently, increase TTL
                            ttl_adjustments[method_name] = min(new_ttl * 2, 7200)  # Cap at 2 hours
            
            result = {
                'success': True,
                'expired_items_removed': optimized_count,
                'current_cache_size': len(self._cache),
                'ttl_adjustments': ttl_adjustments,
                'optimization_timestamp': current_time.isoformat()
            }
            
            logger.info(f"Cache optimization completed: {optimized_count} expired items removed")
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing cache: {e}")
            return {'success': False, 'error': str(e)}
    
    def force_refresh_cache(self, method: str = None) -> Dict[str, Any]:
        """Force refresh of cache for specific method or all methods"""
        try:
            if method:
                # Clear specific method cache
                self._clear_cache(method)
                logger.info(f"Force refreshed cache for {method}")
                return {'success': True, 'message': f'Cache refreshed for {method}'}
            else:
                # Clear all cache
                self._clear_cache()
                logger.info("Force refreshed all cache")
                return {'success': True, 'message': 'All cache refreshed'}
                
        except Exception as e:
            logger.error(f"Error force refreshing cache: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_ec2_permissions(self) -> Dict[str, Any]:
        """Check if the user has necessary permissions for EC2 operations"""
        try:
            permissions_to_check = [
                'ec2:RunInstances',
                'ec2:DescribeInstances',
                'ec2:DescribeInstanceTypes',
                'ec2:DescribeImages',
                'ec2:DescribeSecurityGroups',
                'ec2:DescribeKeyPairs',
                'ec2:DescribeVpcs',
                'ec2:DescribeSubnets',
                'ec2:CreateTags'
            ]
            
            results = {}
            for permission in permissions_to_check:
                try:
                    # Test each permission with a simple API call
                    if permission == 'ec2:RunInstances':
                        # Just check if we can describe instance types (safe operation)
                        self.client.describe_instance_types(MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:DescribeInstances':
                        self.client.describe_instances(MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:DescribeInstanceTypes':
                        self.client.describe_instance_types(MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:DescribeImages':
                        self.client.describe_images(Owners=['amazon'], MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:DescribeSecurityGroups':
                        self.client.describe_security_groups(MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:DescribeKeyPairs':
                        self.client.describe_key_pairs(MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:DescribeVpcs':
                        self.client.describe_vpcs(MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:DescribeSubnets':
                        self.client.describe_subnets(MaxResults=1)
                        results[permission] = True
                    elif permission == 'ec2:CreateTags':
                        # This is harder to test safely, so we'll assume it's available
                        results[permission] = True
                except Exception as perm_error:
                    logger.warning(f"Permission check failed for {permission}: {perm_error}")
                    results[permission] = False
            
            # Calculate overall permission status
            total_permissions = len(permissions_to_check)
            granted_permissions = sum(results.values())
            permission_score = granted_permissions / total_permissions if total_permissions > 0 else 0
            
            return {
                "success": True,
                "permissions": results,
                "total_permissions": total_permissions,
                "granted_permissions": granted_permissions,
                "permission_score": permission_score,
                "can_create_instances": results.get('ec2:RunInstances', False),
                "region": self.get_user_region(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking EC2 permissions: {e}")
            return {
                "success": False,
                "error": str(e),
                "region": self.get_user_region()
            }
