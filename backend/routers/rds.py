"""
RDS API Router
Handles RDS database instance management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from database import get_db, User
from services.aws.rds_service import RDSService
from utils.auth import get_current_active_user

router = APIRouter()


class RDSInstanceCreateRequest(BaseModel):
    db_instance_identifier: str = Field(..., min_length=1, max_length=63, description="RDS instance identifier")
    db_instance_class: str = Field(..., description="RDS instance class (e.g., db.t3.micro)")
    engine: str = Field(..., description="Database engine (mysql, postgres, etc.)")
    master_username: str = Field(..., min_length=1, description="Master username")
    master_user_password: str = Field(..., min_length=8, description="Master password")
    allocated_storage: Optional[int] = Field(20, ge=20, description="Allocated storage in GB")
    engine_version: Optional[str] = Field(None, description="Engine version")
    db_name: Optional[str] = Field(None, description="Database name")


@router.get("/instances")
async def list_db_instances(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all RDS database instances"""
    try:
        rds_service = RDSService(db, current_user.id)
        result = rds_service.list_db_instances()
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list RDS instances'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{db_instance_identifier}")
async def get_db_instance(
    db_instance_identifier: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get RDS instance details"""
    try:
        rds_service = RDSService(db, current_user.id)
        result = rds_service.get_db_instance(db_instance_identifier)
        
        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error', 'Instance not found'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances")
async def create_db_instance(
    instance_data: RDSInstanceCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new RDS database instance"""
    try:
        rds_service = RDSService(db, current_user.id)
        result = rds_service.create_db_instance(instance_data.dict())
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to create RDS instance'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/instances/{db_instance_identifier}")
async def delete_db_instance(
    db_instance_identifier: str,
    skip_final_snapshot: bool = Query(True, description="Skip final snapshot"),
    final_snapshot_identifier: Optional[str] = Query(None, description="Final snapshot identifier"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an RDS database instance"""
    try:
        rds_service = RDSService(db, current_user.id)
        result = rds_service.delete_db_instance(
            db_instance_identifier,
            skip_final_snapshot=skip_final_snapshot,
            final_snapshot_identifier=final_snapshot_identifier
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to delete RDS instance'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
