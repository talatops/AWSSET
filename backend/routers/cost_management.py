"""
Cost Management API Router
Handles budget monitoring, cost optimization, and unused resource detection
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, User
from services.aws.cost_optimization_service import CostOptimizationService
from services.aws.billing_service import AWSBillingService
from utils.auth import get_current_active_user

router = APIRouter()


@router.get("/budgets")
async def get_budget_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current budget status and alerts"""
    try:
        cost_service = CostOptimizationService(db, current_user.id)
        result = await cost_service.get_budget_status()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unused-resources")
async def detect_unused_resources(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Detect unused or underutilized AWS resources"""
    try:
        cost_service = CostOptimizationService(db, current_user.id)
        result = await cost_service.detect_unused_resources()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimization-recommendations")
async def get_optimization_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get cost optimization recommendations"""
    try:
        cost_service = CostOptimizationService(db, current_user.id)
        result = await cost_service.get_cost_optimization_recommendations()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current-costs")
async def get_current_costs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current month costs"""
    try:
        from services.aws.credential_manager import AWSCredentialManager
        credential_manager = AWSCredentialManager()
        credentials = credential_manager.get_credentials(db, current_user.id)
        
        if not credentials:
            raise HTTPException(status_code=400, detail="AWS credentials not configured")
        
        billing_service = AWSBillingService(credentials)
        result = await billing_service.get_current_month_costs()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
