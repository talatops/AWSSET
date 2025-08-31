"""
EC2 Router
API endpoints for EC2 instance management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from database import get_db, User
from services.aws.ec2_service import EC2Service
from utils.auth import get_current_active_user
from utils.logger import get_aws_logger

logger = get_aws_logger()
router = APIRouter()

# =========================================================================
# PYDANTIC MODELS
# =========================================================================

class InstanceFilters(BaseModel):
    state: Optional[str] = Field(None, description="Filter by instance state")
    tag: Optional[str] = Field(None, description="Filter by tag (format: key:value)")

class CreateInstanceRequest(BaseModel):
    name: Optional[str] = Field(None, description="Instance name")
    image_id: str = Field(..., description="AMI ID")
    instance_type: str = Field(..., description="Instance type (e.g., t2.micro)")
    key_name: Optional[str] = Field(None, description="Key pair name")
    security_group_ids: Optional[List[str]] = Field(None, description="Security group IDs")
    security_groups: Optional[List[str]] = Field(None, description="Security group names")
    subnet_id: Optional[str] = Field(None, description="Subnet ID")
    user_data: Optional[str] = Field(None, description="User data script")
    iam_instance_profile: Optional[Dict[str, str]] = Field(None, description="IAM instance profile")
    min_count: Optional[int] = Field(1, ge=1, le=10, description="Minimum number of instances")
    max_count: Optional[int] = Field(1, ge=1, le=10, description="Maximum number of instances")
    # Advanced volume configuration
    volume_size: Optional[int] = Field(8, ge=1, le=16384, description="Root volume size in GB")
    volume_type: Optional[str] = Field("gp3", description="Volume type (gp2, gp3, io1, io2, st1, sc1)")
    volume_encrypted: Optional[bool] = Field(False, description="Enable volume encryption")

class InstanceActionRequest(BaseModel):
    force: Optional[bool] = Field(False, description="Force the action")

class AMIFilters(BaseModel):
    name: Optional[str] = Field(None, description="Filter by AMI name")
    architecture: Optional[str] = Field(None, description="Filter by architecture")
    state: Optional[str] = Field("available", description="Filter by state")

# =========================================================================
# CACHE MONITORING ENDPOINTS
# =========================================================================

@router.get("/cache/statistics")
async def get_cache_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get EC2 service cache statistics and health information
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        cache_stats = ec2_service.get_cache_statistics()
        return cache_stats
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )

@router.post("/cache/optimize")
async def optimize_cache(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Optimize EC2 service cache by removing expired items and adjusting TTL
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.optimize_cache()
        return result
    except Exception as e:
        logger.error(f"Error optimizing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize cache"
        )

@router.post("/cache/refresh")
async def force_refresh_cache(
    method: Optional[str] = Query(None, description="Specific method to refresh, or all if not specified"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Force refresh of EC2 service cache for specific method or all methods
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.force_refresh_cache(method)
        return result
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh cache"
        )

@router.get("/instance-types/{instance_type}/availability")
async def check_instance_type_availability(
    instance_type: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if an instance type is available in the current region
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.check_instance_type_availability(instance_type)
        return result
    except Exception as e:
        logger.error(f"Error checking instance type availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check instance type availability"
        )

@router.get("/permissions")
async def check_ec2_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if the user has necessary permissions for EC2 operations
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.check_ec2_permissions()
        return result
    except Exception as e:
        logger.error(f"Error checking EC2 permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check EC2 permissions"
        )

# =========================================================================
# INSTANCE ENDPOINTS
# =========================================================================

@router.get("/instances")
async def list_instances(
    state: Optional[str] = Query(None, description="Filter by instance state"),
    tag: Optional[str] = Query(None, description="Filter by tag (format: key:value)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List EC2 instances for the current user
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        
        filters = {}
        if state:
            filters['state'] = state
        if tag:
            filters['tag'] = tag
        
        result = ec2_service.list_instances(filters if filters else None)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to list instances')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing instances for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing instances"
        )

@router.post("/instances")
async def create_instance(
    instance_config: CreateInstanceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new EC2 instance
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        
        # Convert Pydantic model to dict for the service
        config_dict = {
            'ImageId': instance_config.image_id,
            'InstanceType': instance_config.instance_type,
            'MinCount': instance_config.min_count,
            'MaxCount': instance_config.max_count,
        }
        
        # Add optional parameters
        if instance_config.name:
            config_dict['Name'] = instance_config.name
        if instance_config.key_name:
            config_dict['KeyName'] = instance_config.key_name
        if instance_config.security_group_ids:
            config_dict['SecurityGroupIds'] = instance_config.security_group_ids
        if instance_config.security_groups:
            config_dict['SecurityGroups'] = instance_config.security_groups
        if instance_config.subnet_id:
            config_dict['SubnetId'] = instance_config.subnet_id
        if instance_config.user_data:
            config_dict['UserData'] = instance_config.user_data
        if instance_config.iam_instance_profile:
            config_dict['IamInstanceProfile'] = instance_config.iam_instance_profile
        
        # Add advanced volume configuration
        if hasattr(instance_config, 'volume_size') and instance_config.volume_size:
            config_dict['VolumeSize'] = instance_config.volume_size
        if hasattr(instance_config, 'volume_type') and instance_config.volume_type:
            config_dict['VolumeType'] = instance_config.volume_type
        if hasattr(instance_config, 'volume_encrypted') and instance_config.volume_encrypted is not None:
            config_dict['VolumeEncrypted'] = instance_config.volume_encrypted
        
        # Log the configuration being sent
        logger.info(f"Creating EC2 instance with config: {config_dict}")
        
        result = ec2_service.create_instance(config_dict)
        
        if result['success']:
            logger.info(f"EC2 instance creation successful: {result}")
            return result
        else:
            error_msg = result.get('error_message', result.get('error', 'Failed to create instance'))
            logger.error(f"EC2 instance creation failed: {error_msg}")
            logger.error(f"Config: {config_dict}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating instance for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the instance"
        )

@router.get("/instances/{instance_id}")
async def get_instance(
    instance_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific instance
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.get_instance(instance_id)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', 'Instance not found')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instance {instance_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the instance"
        )

@router.post("/instances/{instance_id}/start")
async def start_instance(
    instance_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start an EC2 instance
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.start_instance(instance_id)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to start instance')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting instance {instance_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while starting the instance"
        )

@router.post("/instances/{instance_id}/stop")
async def stop_instance(
    instance_id: str,
    action_config: Optional[InstanceActionRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Stop an EC2 instance
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        force = action_config.force if action_config else False
        result = ec2_service.stop_instance(instance_id, force=force)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to stop instance')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping instance {instance_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while stopping the instance"
        )

@router.post("/instances/{instance_id}/reboot")
async def reboot_instance(
    instance_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reboot an EC2 instance
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.reboot_instance(instance_id)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to reboot instance')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebooting instance {instance_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while rebooting the instance"
        )

@router.delete("/instances/{instance_id}")
async def terminate_instance(
    instance_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Terminate an EC2 instance
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.terminate_instance(instance_id)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to terminate instance')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error terminating instance {instance_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while terminating the instance"
        )

# =========================================================================
# SECURITY GROUPS
# =========================================================================

@router.get("/security-groups")
async def list_security_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List security groups
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.list_security_groups()
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to list security groups')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing security groups for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing security groups"
        )

# =========================================================================
# KEY PAIRS
# =========================================================================

@router.get("/key-pairs")
async def list_key_pairs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List EC2 key pairs
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.list_key_pairs()
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to list key pairs')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing key pairs for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing key pairs"
        )

@router.post("/key-pairs")
async def create_key_pair(
    key_pair_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new EC2 key pair
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.create_key_pair(
            key_name=key_pair_data.get('key_name'),
            key_type=key_pair_data.get('key_type', 'rsa')
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to create key pair')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating key pair for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating key pair"
        )

@router.delete("/key-pairs/{key_name}")
async def delete_key_pair(
    key_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an EC2 key pair
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.delete_key_pair(key_name)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to delete key pair')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting key pair for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting key pair"
        )

# =========================================================================
# INSTANCE TYPES, VPC, AND SUBNET ENDPOINTS
# =========================================================================

@router.get("/instance-types")
async def list_instance_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List available EC2 instance types with specifications
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.list_instance_types()
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to list instance types')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing instance types for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing instance types"
        )

@router.get("/vpcs")
async def list_vpcs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List available VPCs in the region
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.list_vpcs()
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to list VPCs')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing VPCs for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing VPCs"
        )

@router.get("/subnets")
async def list_subnets(
    vpc_id: Optional[str] = Query(None, description="Filter subnets by VPC ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List available subnets, optionally filtered by VPC
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        result = ec2_service.list_subnets(vpc_id)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to list subnets')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing subnets for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing subnets"
        )

# =========================================================================
# AMIS
# =========================================================================

@router.get("/amis")
async def list_amis(
    name: Optional[str] = Query(None, description="Filter by AMI name"),
    architecture: Optional[str] = Query(None, description="Filter by architecture"),
    ami_state: Optional[str] = Query("available", description="Filter by state"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List available AMIs
    """
    try:
        ec2_service = EC2Service(db, current_user.id)
        
        filters = {}
        if name:
            filters['name'] = name
        if architecture:
            filters['architecture'] = architecture
        if ami_state:
            filters['state'] = ami_state
        
        result = ec2_service.list_amis(filters if filters else None)
        
        if result['success']:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error_message', 'Failed to list AMIs')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing AMIs for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing AMIs"
        )
