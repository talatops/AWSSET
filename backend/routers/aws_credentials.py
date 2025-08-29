"""
AWS Credentials Router
API endpoints for managing AWS credentials
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from database import get_db
from services.aws.credential_manager import AWSCredentialManager
from utils.auth import get_current_active_user
from utils.logger import get_aws_logger
from database import User

logger = get_aws_logger()
router = APIRouter()

# Pydantic models
class AWSCredentialsRequest(BaseModel):
    access_key: str = Field(..., min_length=16, max_length=128, description="AWS Access Key ID")
    secret_key: str = Field(..., min_length=16, max_length=128, description="AWS Secret Access Key")
    region: Optional[str] = Field(None, description="AWS Region")

class AWSCredentialsResponse(BaseModel):
    success: bool
    message: str
    has_credentials: bool
    region: Optional[str] = None
    account_info: Optional[Dict[str, Any]] = None

class AWSValidationResponse(BaseModel):
    success: bool
    valid: bool
    account_info: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AWSRegionsResponse(BaseModel):
    success: bool
    regions: Dict[str, str]

@router.post("/credentials", response_model=AWSCredentialsResponse)
async def store_aws_credentials(
    credentials: AWSCredentialsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Store AWS credentials for the current user
    """
    try:
        credential_manager = AWSCredentialManager()
        
        success = credential_manager.store_credentials(
            db=db,
            user_id=current_user.id,
            access_key=credentials.access_key,
            secret_key=credentials.secret_key,
            region=credentials.region
        )
        
        if success:
            # Get updated user info
            db.refresh(current_user)
            
            # Test the credentials to get account info
            is_valid, validation_info = credential_manager.validate_credentials(
                credentials.access_key, 
                credentials.secret_key, 
                credentials.region
            )
            
            return AWSCredentialsResponse(
                success=True,
                message="AWS credentials stored successfully",
                has_credentials=True,
                region=current_user.aws_region,
                account_info=validation_info if is_valid else None
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to store AWS credentials. Please check your credentials and try again."
            )
            
    except Exception as e:
        logger.error(f"Error storing AWS credentials for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while storing your AWS credentials"
        )

@router.get("/credentials", response_model=AWSCredentialsResponse)
async def get_aws_credentials_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get AWS credentials status for the current user (without exposing actual credentials)
    """
    try:
        credential_manager = AWSCredentialManager()
        
        # Check if user has credentials stored
        credentials = credential_manager.get_credentials(db, current_user.id)
        has_credentials = credentials is not None
        
        account_info = None
        if has_credentials:
            # Test credentials and get account info
            is_valid, validation_info = credential_manager.validate_credentials(
                credentials['aws_access_key_id'],
                credentials['aws_secret_access_key'],
                credentials['region_name']
            )
            
            if is_valid:
                account_info = validation_info
        
        return AWSCredentialsResponse(
            success=True,
            message="AWS credentials status retrieved",
            has_credentials=has_credentials,
            region=current_user.aws_region,
            account_info=account_info
        )
        
    except Exception as e:
        logger.error(f"Error getting AWS credentials status for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking your AWS credentials"
        )

@router.post("/validate", response_model=AWSValidationResponse)
async def validate_aws_credentials(
    credentials: AWSCredentialsRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate AWS credentials without storing them
    """
    try:
        credential_manager = AWSCredentialManager()
        
        is_valid, validation_info = credential_manager.validate_credentials(
            credentials.access_key,
            credentials.secret_key,
            credentials.region
        )
        
        return AWSValidationResponse(
            success=True,
            valid=is_valid,
            account_info=validation_info if is_valid else None,
            error=validation_info.get('error_message') if not is_valid else None
        )
        
    except Exception as e:
        logger.error(f"Error validating AWS credentials for user {current_user.id}: {e}")
        return AWSValidationResponse(
            success=False,
            valid=False,
            error="An error occurred while validating your AWS credentials"
        )

@router.post("/test-permissions", response_model=Dict[str, Any])
async def test_aws_permissions(
    credentials: Optional[AWSCredentialsRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    service: str = "ec2"
):
    """
    Test AWS permissions for a specific service
    Can accept credentials in request body (for setup wizard) or use stored credentials
    """
    try:
        credential_manager = AWSCredentialManager()
        
        # Use provided credentials or get stored ones
        if credentials:
            # Use credentials from request (setup wizard)
            test_credentials = {
                'aws_access_key_id': credentials.access_key,
                'aws_secret_access_key': credentials.secret_key,
                'region_name': credentials.region or 'us-east-1'
            }
        else:
            # Use stored credentials
            stored_credentials = credential_manager.get_credentials(db, current_user.id)
            if not stored_credentials:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No AWS credentials found. Please configure your credentials first."
                )
            test_credentials = stored_credentials
        
        # Test permissions using the credential manager's validate and test methods
        permission_results = credential_manager.test_service_permissions(
            test_credentials['aws_access_key_id'],
            test_credentials['aws_secret_access_key'],
            test_credentials['region_name'],
            service
        )
        
        return permission_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing AWS permissions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while testing your AWS permissions"
        )

@router.delete("/credentials")
async def remove_aws_credentials(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove AWS credentials for the current user
    """
    try:
        credential_manager = AWSCredentialManager()
        
        success = credential_manager.remove_credentials(db, current_user.id)
        
        if success:
            return {"success": True, "message": "AWS credentials removed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove AWS credentials"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing AWS credentials for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while removing your AWS credentials"
        )

@router.get("/regions", response_model=AWSRegionsResponse)
async def get_aws_regions():
    """
    Get list of available AWS regions
    """
    try:
        credential_manager = AWSCredentialManager()
        regions = credential_manager.get_available_regions()
        
        return AWSRegionsResponse(
            success=True,
            regions=regions
        )
        
    except Exception as e:
        logger.error(f"Error getting AWS regions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching AWS regions"
        )

@router.put("/region")
async def update_aws_region(
    region: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update the default AWS region for the current user
    """
    try:
        # Update user's default region
        current_user.aws_region = region
        db.commit()
        
        return {
            "success": True,
            "message": f"Default AWS region updated to {region}",
            "region": region
        }
        
    except Exception as e:
        logger.error(f"Error updating AWS region for user {current_user.id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating your AWS region"
        )
