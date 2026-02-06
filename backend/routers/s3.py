"""
S3 API Router
Handles S3 bucket and object management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from database import get_db, User
from services.aws.s3_service import S3Service
from utils.auth import get_current_active_user

router = APIRouter()


class BucketCreateRequest(BaseModel):
    bucket_name: str = Field(..., min_length=3, max_length=63, description="S3 bucket name")
    region: Optional[str] = Field(None, description="AWS region for bucket")


@router.get("/buckets")
async def list_buckets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all S3 buckets"""
    try:
        s3_service = S3Service(db, current_user.id)
        result = s3_service.list_buckets()
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list buckets'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buckets")
async def create_bucket(
    bucket_data: BucketCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new S3 bucket"""
    try:
        s3_service = S3Service(db, current_user.id)
        result = s3_service.create_bucket(bucket_data.bucket_name, bucket_data.region)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to create bucket'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/buckets/{bucket_name}")
async def delete_bucket(
    bucket_name: str,
    force: bool = Query(False, description="Force delete by removing all objects first"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an S3 bucket"""
    try:
        s3_service = S3Service(db, current_user.id)
        result = s3_service.delete_bucket(bucket_name, force=force)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to delete bucket'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buckets/{bucket_name}/objects")
async def list_objects(
    bucket_name: str,
    prefix: Optional[str] = Query(None, description="Object key prefix filter"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List objects in an S3 bucket"""
    try:
        s3_service = S3Service(db, current_user.id)
        result = s3_service.list_objects(bucket_name, prefix)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list objects'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
