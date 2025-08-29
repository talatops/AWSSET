# AWS Chatbot - Technical Specifications for Next Features

## 🏗️ **System Architecture Overview**

### **Current Architecture**
```
Frontend (React) ←→ WebSocket ←→ Backend (FastAPI)
                                      ↓
                                 AWS Services
                                 (EC2, S3, IAM, etc.)
                                      ↓
                                 PostgreSQL Database
```

### **Enhanced Architecture (After Implementation)**
```
Frontend (React) ←→ WebSocket ←→ Backend (FastAPI)
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              AI Analysis        Cost Services     Notification
              (CloudTrail)      (Cost Explorer)      System
                    ↓                 ↓                 ↓
               Groq API         AWS Cost APIs      Email/Slack/SMS
                    ↓                 ↓                 ↓
              PostgreSQL       Cache Layer       Notification Queue
```

---

## 🧠 **1. CloudTrail AI Analysis - Technical Specification**

### **Backend Implementation**

#### **1.1 CloudTrail Service** (`backend/services/aws/cloudtrail_service.py`)
```python
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from utils.logger import get_aws_logger

class CloudTrailService(AWSBaseClient):
    """
    AWS CloudTrail integration for log analysis and security monitoring
    """
    
    def __init__(self, db: Session, user_id: int):
        super().__init__(db, user_id, "cloudtrail")
        self.lookup_client = self.session.client('cloudtrail') if self.session else None
        
    async def fetch_events(
        self, 
        start_time: datetime,
        end_time: datetime,
        max_events: int = 1000,
        event_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch CloudTrail events for analysis
        
        Args:
            start_time: Start time for event lookup
            end_time: End time for event lookup  
            max_events: Maximum number of events to fetch
            event_name: Optional filter for specific event names
            
        Returns:
            Dict containing events and metadata
        """
        try:
            lookup_attributes = []
            if event_name:
                lookup_attributes.append({
                    'AttributeKey': 'EventName',
                    'AttributeValue': event_name
                })
            
            paginator = self.lookup_client.get_paginator('lookup_events')
            page_iterator = paginator.paginate(
                LookupAttributes=lookup_attributes,
                StartTime=start_time,
                EndTime=end_time,
                MaxItems=max_events
            )
            
            all_events = []
            for page in page_iterator:
                all_events.extend(page.get('Events', []))
                
            return {
                'success': True,
                'events': all_events,
                'count': len(all_events),
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
        except ClientError as e:
            logger.error(f"CloudTrail lookup failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'events': []
            }
    
    def categorize_events(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize events by type for targeted analysis
        """
        categories = {
            'authentication': [],
            'resource_creation': [],
            'resource_deletion': [],
            'permission_changes': [],
            'data_access': [],
            'cost_events': [],
            'security_events': []
        }
        
        # Authentication events
        auth_events = ['ConsoleLogin', 'AssumeRole', 'GetSessionToken']
        # Resource creation events  
        creation_events = ['RunInstances', 'CreateBucket', 'CreateFunction']
        # Security-sensitive events
        security_events = ['PutBucketPolicy', 'AttachUserPolicy', 'CreateAccessKey']
        
        for event in events:
            event_name = event.get('EventName', '')
            
            if event_name in auth_events:
                categories['authentication'].append(event)
            elif any(create_word in event_name for create_word in ['Create', 'Run', 'Launch']):
                categories['resource_creation'].append(event)
            elif any(delete_word in event_name for delete_word in ['Delete', 'Terminate']):
                categories['resource_deletion'].append(event)
            elif event_name in security_events:
                categories['security_events'].append(event)
            elif 'Policy' in event_name or 'Role' in event_name:
                categories['permission_changes'].append(event)
            else:
                # Default category based on service
                service_name = event.get('EventSource', '').split('.')[0]
                if service_name in ['s3', 'dynamodb']:
                    categories['data_access'].append(event)
                else:
                    categories['cost_events'].append(event)
                    
        return categories
```

#### **1.2 AI Analysis Engine** (`backend/services/ai/cloudtrail_analyzer.py`)
```python
from typing import Dict, List, Any
import json
from datetime import datetime
from services.ai.gemini_service import groq_service
from utils.logger import get_aws_logger

class CloudTrailAIAnalyzer:
    """
    AI-powered analysis of CloudTrail logs using Groq
    """
    
    def __init__(self):
        self.groq_service = groq_service
        self.logger = get_aws_logger()
        
    async def analyze_security_events(self, events: List[Dict]) -> Dict[str, Any]:
        """
        Analyze events for security anomalies and threats
        """
        if not events:
            return {'findings': [], 'risk_level': 'LOW', 'summary': 'No events to analyze'}
            
        # Prepare events for AI analysis
        event_summary = self._prepare_events_for_analysis(events, max_events=50)
        
        security_prompt = f"""
        You are a cybersecurity expert analyzing AWS CloudTrail events. 
        Analyze these events for security threats and anomalies:

        EVENTS:
        {json.dumps(event_summary, indent=2)}

        Identify and report:
        1. Suspicious authentication patterns (unusual locations, times, failures)
        2. Privilege escalation attempts
        3. Unusual API access patterns
        4. Data exfiltration indicators
        5. Resource abuse or cryptomining activities

        Respond with JSON:
        {{
            "findings": [
                {{
                    "type": "authentication_anomaly|privilege_escalation|data_access|resource_abuse",
                    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
                    "description": "Clear description of the finding",
                    "evidence": ["list of supporting evidence"],
                    "recommendations": ["list of recommended actions"]
                }}
            ],
            "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
            "summary": "Overall security assessment summary"
        }}
        """
        
        try:
            response = await self.groq_service._call_groq(security_prompt)
            analysis = json.loads(response)
            
            # Add metadata
            analysis['analyzed_events'] = len(events)
            analysis['analysis_time'] = datetime.utcnow().isoformat()
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            return {
                'findings': [],
                'risk_level': 'UNKNOWN',
                'summary': f'Analysis failed: {str(e)}',
                'error': str(e)
            }
    
    async def analyze_cost_anomalies(self, events: List[Dict]) -> Dict[str, Any]:
        """
        Analyze events for cost-related anomalies and spending spikes
        """
        cost_relevant_events = self._filter_cost_events(events)
        
        cost_prompt = f"""
        You are an AWS cost optimization expert. Analyze these CloudTrail events 
        to identify what might cause cost increases or spikes:

        EVENTS:
        {json.dumps(cost_relevant_events, indent=2)}

        Analyze for:
        1. Large resource provisioning (big instances, many resources)
        2. Data transfer activities (cross-region, internet)
        3. Premium service usage (Reserved Instances, Spot terminations)
        4. Unusual scaling patterns
        5. Resource creation without corresponding deletion

        Respond with JSON:
        {{
            "cost_drivers": [
                {{
                    "category": "compute|storage|network|premium_services",
                    "impact": "LOW|MEDIUM|HIGH",
                    "description": "What happened that affects costs",
                    "estimated_impact": "Rough cost estimate if possible",
                    "recommendations": ["How to optimize or prevent"]
                }}
            ],
            "summary": "Overall cost impact assessment",
            "optimization_opportunities": ["List of cost saving suggestions"]
        }}
        """
        
        try:
            response = await self.groq_service._call_groq(cost_prompt)
            analysis = json.loads(response)
            
            analysis['analyzed_events'] = len(cost_relevant_events)
            analysis['analysis_time'] = datetime.utcnow().isoformat()
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Cost analysis failed: {e}")
            return {
                'cost_drivers': [],
                'summary': f'Analysis failed: {str(e)}',
                'optimization_opportunities': [],
                'error': str(e)
            }
    
    def _prepare_events_for_analysis(self, events: List[Dict], max_events: int = 50) -> List[Dict]:
        """
        Prepare events for AI analysis by extracting key fields
        """
        prepared_events = []
        
        for event in events[:max_events]:  # Limit to avoid token limits
            prepared_event = {
                'event_name': event.get('EventName'),
                'event_time': event.get('EventTime', '').isoformat() if hasattr(event.get('EventTime', ''), 'isoformat') else str(event.get('EventTime')),
                'user_identity': self._extract_user_identity(event),
                'source_ip': event.get('SourceIPAddress'),
                'user_agent': event.get('UserAgent'),
                'aws_region': event.get('AwsRegion'),
                'error_code': event.get('ErrorCode'),
                'error_message': event.get('ErrorMessage'),
                'resources': self._extract_resources(event)
            }
            prepared_events.append(prepared_event)
            
        return prepared_events
    
    def _extract_user_identity(self, event: Dict) -> Dict:
        """Extract user identity information"""
        user_identity = event.get('UserIdentity', {})
        return {
            'type': user_identity.get('type'),
            'user_name': user_identity.get('userName'),
            'arn': user_identity.get('arn'),
            'account_id': user_identity.get('accountId')
        }
    
    def _extract_resources(self, event: Dict) -> List[Dict]:
        """Extract resource information"""
        resources = event.get('Resources', [])
        return [
            {
                'name': resource.get('ResourceName'),
                'type': resource.get('ResourceType')
            }
            for resource in resources
        ]
    
    def _filter_cost_events(self, events: List[Dict]) -> List[Dict]:
        """Filter events that are likely to impact costs"""
        cost_event_patterns = [
            'RunInstances', 'CreateBucket', 'CreateFunction', 'CreateDBInstance',
            'ModifyDBInstance', 'CreateVolume', 'CreateSnapshot', 'CreateImage',
            'RequestSpotInstances', 'PurchaseReservedInstancesOffering'
        ]
        
        return [
            event for event in events
            if any(pattern in event.get('EventName', '') for pattern in cost_event_patterns)
        ]
```

#### **1.3 Database Models** (`backend/models/cloudtrail.py`)
```python
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class CloudTrailAnalysis(Base):
    """Store CloudTrail analysis results for caching and history"""
    __tablename__ = "cloudtrail_analysis"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # security, cost, performance
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    events_count = Column(Integer, default=0)
    findings = Column(JSON)  # Store analysis results
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="cloudtrail_analyses")

class SecurityFinding(Base):
    """Individual security findings from CloudTrail analysis"""
    __tablename__ = "security_findings"
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("cloudtrail_analysis.id"))
    finding_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON)  # Supporting evidence
    recommendations = Column(JSON)  # Recommended actions
    status = Column(String(20), default='OPEN')  # OPEN, INVESTIGATING, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = relationship("CloudTrailAnalysis")
```

### **Frontend Implementation**

#### **1.4 CloudTrail Analysis Component** (`frontend/src/components/analysis/CloudTrailAnalysis.js`)
```jsx
import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button, 
  Select, MenuItem, FormControl, InputLabel, Alert,
  Chip, LinearProgress, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import {
  Security, Assessment, TrendingUp, ExpandMore,
  Warning, Error, Info, CheckCircle
} from '@mui/icons-material';
import { motion } from 'framer-motion';

const CloudTrailAnalysis = () => {
  const [analysisType, setAnalysisType] = useState('security');
  const [timeRange, setTimeRange] = useState('24h');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analysisTypes = [
    { value: 'security', label: 'Security Analysis', icon: <Security /> },
    { value: 'cost', label: 'Cost Analysis', icon: <TrendingUp /> },
    { value: 'performance', label: 'Performance Analysis', icon: <Assessment /> }
  ];

  const timeRanges = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ];

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/cloudtrail/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          analysis_type: analysisType,
          time_range: timeRange
        })
      });
      
      if (!response.ok) {
        throw new Error('Analysis failed');
      }
      
      const results = await response.json();
      setAnalysisResults(results);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return <Error />;
      case 'HIGH': return <Warning />;
      case 'MEDIUM': return <Info />;
      case 'LOW': return <CheckCircle />;
      default: return <Info />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        CloudTrail AI Analysis
      </Typography>
      
      {/* Analysis Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Analysis Type</InputLabel>
                <Select
                  value={analysisType}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  label="Analysis Type"
                >
                  {analysisTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {type.icon}
                        {type.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Time Range</InputLabel>
                <Select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  label="Time Range"
                >
                  {timeRanges.map((range) => (
                    <MenuItem key={range.value} value={range.value}>
                      {range.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Button
                variant="contained"
                onClick={runAnalysis}
                disabled={loading}
                fullWidth
                sx={{ py: 2 }}
              >
                {loading ? 'Analyzing...' : 'Run Analysis'}
              </Button>
            </Grid>
          </Grid>
          
          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Analyzing CloudTrail logs with AI...
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Analysis Results */}
      {analysisResults && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Summary Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Analysis Summary</Typography>
                <Chip
                  label={analysisResults.risk_level || 'UNKNOWN'}
                  color={getSeverityColor(analysisResults.risk_level)}
                  icon={getSeverityIcon(analysisResults.risk_level)}
                />
              </Box>
              
              <Typography variant="body1" paragraph>
                {analysisResults.summary}
              </Typography>
              
              <Box display="flex" gap={2} flexWrap="wrap">
                <Chip 
                  label={`${analysisResults.analyzed_events || 0} events analyzed`}
                  variant="outlined"
                />
                <Chip 
                  label={`${analysisResults.findings?.length || 0} findings`}
                  variant="outlined"
                />
                <Chip 
                  label={new Date(analysisResults.analysis_time).toLocaleString()}
                  variant="outlined"
                />
              </Box>
            </CardContent>
          </Card>

          {/* Findings */}
          {analysisResults.findings && analysisResults.findings.length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Detailed Findings
                </Typography>
                
                {analysisResults.findings.map((finding, index) => (
                  <Accordion key={index} sx={{ mb: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Box display="flex" alignItems="center" gap={2} width="100%">
                        {getSeverityIcon(finding.severity)}
                        <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                          {finding.description}
                        </Typography>
                        <Chip
                          label={finding.severity}
                          size="small"
                          color={getSeverityColor(finding.severity)}
                        />
                      </Box>
                    </AccordionSummary>
                    
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom>
                            Evidence:
                          </Typography>
                          <ul>
                            {finding.evidence?.map((evidence, i) => (
                              <li key={i}>
                                <Typography variant="body2">{evidence}</Typography>
                              </li>
                            ))}
                          </ul>
                        </Grid>
                        
                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" gutterBottom>
                            Recommendations:
                          </Typography>
                          <ul>
                            {finding.recommendations?.map((rec, i) => (
                              <li key={i}>
                                <Typography variant="body2">{rec}</Typography>
                              </li>
                            ))}
                          </ul>
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </CardContent>
            </Card>
          )}
        </motion.div>
      )}
    </Box>
  );
};

export default CloudTrailAnalysis;
```

### **API Endpoints**

#### **1.5 CloudTrail Router** (`backend/routers/cloudtrail.py`)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from utils.auth import get_current_user
from services.aws.cloudtrail_service import CloudTrailService
from services.ai.cloudtrail_analyzer import CloudTrailAIAnalyzer
from database import get_db, User

router = APIRouter(prefix="/api/cloudtrail", tags=["CloudTrail Analysis"])

class AnalysisRequest(BaseModel):
    analysis_type: str  # security, cost, performance
    time_range: str     # 1h, 24h, 7d, 30d
    max_events: Optional[int] = 1000

@router.post("/analyze")
async def analyze_cloudtrail_logs(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze CloudTrail logs with AI
    """
    try:
        # Parse time range
        now = datetime.utcnow()
        time_deltas = {
            '1h': timedelta(hours=1),
            '24h': timedelta(days=1),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }
        
        if request.time_range not in time_deltas:
            raise HTTPException(status_code=400, detail="Invalid time range")
            
        start_time = now - time_deltas[request.time_range]
        
        # Fetch CloudTrail events
        cloudtrail_service = CloudTrailService(db, current_user.id)
        events_result = await cloudtrail_service.fetch_events(
            start_time=start_time,
            end_time=now,
            max_events=request.max_events
        )
        
        if not events_result['success']:
            raise HTTPException(status_code=500, detail=events_result['error'])
        
        # Analyze with AI
        analyzer = CloudTrailAIAnalyzer()
        
        if request.analysis_type == 'security':
            analysis_result = await analyzer.analyze_security_events(events_result['events'])
        elif request.analysis_type == 'cost':
            analysis_result = await analyzer.analyze_cost_anomalies(events_result['events'])
        else:
            raise HTTPException(status_code=400, detail="Unsupported analysis type")
        
        # Store results in database for history
        # ... (database storage logic)
        
        return {
            'success': True,
            'analysis_type': request.analysis_type,
            'time_range': request.time_range,
            'events_analyzed': events_result['count'],
            **analysis_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

This technical specification provides a detailed implementation plan for the CloudTrail AI Analysis feature, including:

1. **Complete backend architecture** with CloudTrail service and AI analyzer
2. **Database models** for storing analysis results
3. **Frontend components** for user interaction and results display
4. **API endpoints** for triggering and retrieving analyses
5. **Error handling** and performance considerations

The implementation follows our existing patterns and integrates seamlessly with the current Groq AI service and WebSocket infrastructure.
