"""
AWS EC2 Service Implementation
Comprehensive EC2 instance management functionality
"""

import boto3
from typing import Dict, List, Any, Optional, Tuple
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from datetime import datetime

from .aws_client import AWSBaseClient
from database import User, AWSResource
from utils.logger import get_aws_logger

logger = get_aws_logger()

class EC2Service(AWSBaseClient):
    """EC2 service implementation for instance management"""
    
    def __init__(self, db: Session, user_id: int):
        super().__init__(db, user_id, "ec2")
        self.resource = self.session.resource('ec2') if self.session else None
    
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
        Create a new EC2 instance
        
        Args:
            instance_config: Instance configuration parameters
            
        Returns:
            Dict containing creation result
        """
        try:
            # Validate required parameters
            required_params = ['ImageId', 'InstanceType']
            for param in required_params:
                if param not in instance_config:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
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
            
            # Launch instance
            response = self.client.run_instances(**launch_params)
            
            instances = []
            for instance in response['Instances']:
                instance_data = self._format_instance_data(instance)
                instances.append(instance_data)
                
                # Track in database
                self._track_aws_resource(
                    resource_type='ec2',
                    resource_id=instance['InstanceId'],
                    resource_name=instance_config.get('Name', ''),
                    resource_arn=f"arn:aws:ec2:{self.get_user_region()}:{instance.get('OwnerId', '')}:instance/{instance['InstanceId']}",
                    status=instance['State']['Name'],
                    meta_data=instance_data,
                    created_via_chat=True
                )
                
                # Add name tag if provided
                if 'Name' in instance_config:
                    try:
                        self.client.create_tags(
                            Resources=[instance['InstanceId']],
                            Tags=[{'Key': 'Name', 'Value': instance_config['Name']}]
                        )
                    except Exception as tag_error:
                        logger.warning(f"Failed to add name tag: {tag_error}")
            
            result = {
                "success": True,
                "instances": instances,
                "count": len(instances),
                "launch_params": launch_params,
                "timestamp": datetime.utcnow().isoformat()
            }
            
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
            
            self._log_operation("list_key_pairs", {"count": len(key_pairs)})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_key_pairs")
    
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
            
            self._log_operation("list_amis", {"count": len(amis), "filters": filters})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_amis", filters)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
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
