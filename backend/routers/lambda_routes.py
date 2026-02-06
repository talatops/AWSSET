"""
Lambda API Router
Handles Lambda function management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from database import get_db, User
from services.aws.lambda_service import LambdaService
from utils.auth import get_current_active_user

router = APIRouter()


@router.get("/functions")
async def list_functions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all Lambda functions"""
    try:
        lambda_service = LambdaService(db, current_user.id)
        result = lambda_service.list_functions()
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to list functions'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/functions/{function_name}")
async def get_function(
    function_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get Lambda function details"""
    try:
        lambda_service = LambdaService(db, current_user.id)
        result = lambda_service.get_function(function_name)
        
        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error', 'Function not found'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/functions/{function_name}/invoke")
async def invoke_function(
    function_name: str,
    payload: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Invoke a Lambda function"""
    try:
        lambda_service = LambdaService(db, current_user.id)
        result = lambda_service.invoke_function(function_name, payload)
        
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to invoke function'))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/functions/{function_name}/metrics")
async def get_function_metrics(
    function_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get CloudWatch metrics for a Lambda function"""
    try:
        lambda_service = LambdaService(db, current_user.id)
        result = lambda_service.get_function_metrics(function_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
