from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from database import get_db, User
from utils.auth import get_current_active_user
from services.aws.credential_manager import AWSCredentialManager
from services.aws.stats_service import AWSStatsService
from utils.logger import get_aws_logger

router = APIRouter()
logger = get_aws_logger()

@router.get("/stats", response_model=Dict[str, Any])
async def get_aws_service_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive AWS service statistics for the current user
    """
    try:
        # Get user's AWS credentials
        credential_manager = AWSCredentialManager()
        credentials = credential_manager.get_credentials(db, current_user.id)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No AWS credentials found. Please configure your credentials first."
            )
        
        # Initialize stats service with user credentials
        stats_service = AWSStatsService(credentials)
        
        # Get all service statistics
        stats = await stats_service.get_all_service_stats()
        
        if not stats.get('success', False):
            logger.warning(f"Failed to fetch complete AWS stats for user {current_user.id}")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching AWS stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching AWS service statistics"
        )

@router.get("/stats/{service_name}", response_model=Dict[str, Any])
async def get_service_specific_stats(
    service_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific AWS service
    """
    try:
        # Validate service name
        valid_services = ['ec2', 's3', 'lambda', 'rds', 'iam', 'bedrock']
        if service_name.lower() not in valid_services:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service name. Valid services: {', '.join(valid_services)}"
            )
        
        # Get user's AWS credentials
        credential_manager = AWSCredentialManager()
        credentials = credential_manager.get_credentials(db, current_user.id)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No AWS credentials found. Please configure your credentials first."
            )
        
        # Initialize stats service
        stats_service = AWSStatsService(credentials)
        
        # Get specific service stats
        all_stats = await stats_service.get_all_service_stats()
        
        service_stats = all_stats.get('services', {}).get(service_name.lower(), {})
        
        return {
            'success': True,
            'service': service_name.lower(),
            'timestamp': all_stats.get('timestamp'),
            'region': all_stats.get('region'),
            'stats': service_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching {service_name} stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching {service_name} statistics"
        )
