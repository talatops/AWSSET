"""
CloudTrail Router
Handles CloudTrail event fetching, analysis, and security insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from database import get_db
from models.cloudtrail import CloudTrailEvent, SecurityIncident, AnomalyDetection, SecurityInsight
from services.aws.cloudtrail_service import CloudTrailService
from services.ai.cloudtrail_ai_service import CloudTrailAIService
from utils.auth import get_current_active_user
from database import User

router = APIRouter(prefix="/api/cloudtrail", tags=["CloudTrail"])

@router.get("/status")
async def get_cloudtrail_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get CloudTrail trail status and configuration"""
    try:
        cloudtrail_service = CloudTrailService(db, current_user.id)
        result = await cloudtrail_service.get_trail_status()
        
        if not result['success']:
            # Provide helpful guidance for common CloudTrail issues
            error_detail = result.get('error', 'Failed to get CloudTrail status')
            if 'No CloudTrail trails found' in error_detail:
                error_detail = {
                    'message': 'No CloudTrail trails found',
                    'guidance': 'To enable CloudTrail: 1) Go to AWS CloudTrail console, 2) Click "Create trail", 3) Configure trail settings, 4) Enable logging for desired regions',
                    'help_url': 'https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-and-update-a-trail.html'
                }
            
            raise HTTPException(status_code=400, detail=error_detail)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CloudTrail status: {str(e)}")

@router.get("/events")
async def get_cloudtrail_events(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    event_names: Optional[List[str]] = Query(None, description="Filter by event names"),
    user_identities: Optional[List[str]] = Query(None, description="Filter by user identities"),
    source_ips: Optional[List[str]] = Query(None, description="Filter by source IP addresses"),
    read_only: Optional[bool] = Query(None, description="Filter by read-only events"),
    management_event: Optional[bool] = Query(None, description="Filter by management events"),
    max_results: int = Query(50, description="Maximum number of events to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch CloudTrail events with filtering"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        cloudtrail_service = CloudTrailService(db, current_user.id)
        result = await cloudtrail_service.fetch_events(
            start_time=start_dt,
            end_time=end_dt,
            event_names=event_names,
            user_identities=user_identities,
            source_ips=source_ips,
            read_only=read_only,
            management_event=management_event,
            max_results=max_results
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to fetch CloudTrail events'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CloudTrail events: {str(e)}")

@router.get("/events/statistics")
async def get_event_statistics(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statistics about CloudTrail events"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        cloudtrail_service = CloudTrailService(db, current_user.id)
        result = await cloudtrail_service.get_event_statistics(
            start_time=start_dt,
            end_time=end_dt
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to get event statistics'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event statistics: {str(e)}")

@router.get("/events/search")
async def search_events(
    query: str = Query(..., description="Search query for events"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    max_results: int = Query(50, description="Maximum number of events to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search CloudTrail events using natural language query"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        cloudtrail_service = CloudTrailService(db, current_user.id)
        result = await cloudtrail_service.search_events(
            query=query,
            start_time=start_dt,
            end_time=end_dt,
            max_results=max_results
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to search events'))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search events: {str(e)}")

@router.post("/analysis/security")
async def analyze_security(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze CloudTrail events for security threats and risks"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        # Fetch events for analysis
        cloudtrail_service = CloudTrailService(db, current_user.id)
        events_result = await cloudtrail_service.fetch_events(
            start_time=start_dt,
            end_time=end_dt,
            max_results=100  # Get more events for better analysis
        )
        
        if not events_result['success']:
            raise HTTPException(status_code=400, detail=events_result.get('error', 'Failed to fetch events for analysis'))
        
        # Analyze events with AI
        ai_service = CloudTrailAIService()
        analysis_result = await ai_service.analyze_security(
            events=events_result['events'],
            time_range=events_result.get('time_range', {})
        )
        
        if not analysis_result['success']:
            raise HTTPException(status_code=400, detail=analysis_result.get('error', 'Failed to analyze events'))
        
        return analysis_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze security: {str(e)}")

@router.post("/analysis/anomalies")
async def detect_anomalies(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    baseline_pattern: str = Query("normal business hours activity", description="Baseline pattern description"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Detect anomalies in CloudTrail events"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        # Fetch events for analysis
        cloudtrail_service = CloudTrailService(db, current_user.id)
        events_result = await cloudtrail_service.fetch_events(
            start_time=start_dt,
            end_time=end_dt,
            max_results=100
        )
        
        if not events_result['success']:
            raise HTTPException(status_code=400, detail=events_result.get('error', 'Failed to fetch events for analysis'))
        
        # Detect anomalies with AI
        ai_service = CloudTrailAIService()
        anomaly_result = await ai_service.detect_anomalies(
            events=events_result['events'],
            baseline_pattern=baseline_pattern
        )
        
        if not anomaly_result['success']:
            raise HTTPException(status_code=400, detail=anomaly_result.get('error', 'Failed to detect anomalies'))
        
        return anomaly_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")

@router.post("/analysis/costs")
async def analyze_costs(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze CloudTrail events for cost implications"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        # Fetch events for analysis
        cloudtrail_service = CloudTrailService(db, current_user.id)
        events_result = await cloudtrail_service.fetch_events(
            start_time=start_dt,
            end_time=end_dt,
            max_results=100
        )
        
        if not events_result['success']:
            raise HTTPException(status_code=400, detail=events_result.get('error', 'Failed to fetch events for analysis'))
        
        # Analyze costs with AI
        ai_service = CloudTrailAIService()
        cost_result = await ai_service.analyze_costs(
            events=events_result['events'],
            time_range=events_result.get('time_range', {})
        )
        
        if not cost_result['success']:
            raise HTTPException(status_code=400, detail=cost_result.get('error', 'Failed to analyze costs'))
        
        return cost_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze costs: {str(e)}")

@router.post("/analysis/comprehensive")
async def generate_comprehensive_report(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive security report from CloudTrail events"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format. Use ISO format.")
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format. Use ISO format.")
        
        # Fetch events for analysis
        cloudtrail_service = CloudTrailService(db, current_user.id)
        events_result = await cloudtrail_service.fetch_events(
            start_time=start_dt,
            end_time=end_dt,
            max_results=200  # Get more events for comprehensive analysis
        )
        
        if not events_result['success']:
            raise HTTPException(status_code=400, detail=events_result.get('error', 'Failed to fetch events for analysis'))
        
        # Generate comprehensive report with AI
        ai_service = CloudTrailAIService()
        report_result = await ai_service.generate_security_report(
            events=events_result['events'],
            time_range=events_result.get('time_range', {})
        )
        
        if not report_result['success']:
            raise HTTPException(status_code=400, detail=report_result.get('error', 'Failed to generate report'))
        
        return report_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comprehensive report: {str(e)}")

@router.get("/health")
async def cloudtrail_health_check():
    """Health check for CloudTrail service"""
    return {
        "status": "healthy",
        "service": "cloudtrail",
        "timestamp": datetime.utcnow().isoformat()
    }
