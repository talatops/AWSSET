"""
CloudTrail AI Analysis Service
Provides AI-powered analysis of CloudTrail events for security insights
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

from .gemini_service import GroqService
from utils.logger import get_aws_logger

logger = get_aws_logger()

class CloudTrailAIService:
    """AI service for CloudTrail event analysis and security insights"""
    
    def __init__(self):
        self.groq_service = GroqService()
        self.analysis_prompts = self._load_analysis_prompts()
    
    def _load_analysis_prompts(self) -> Dict[str, str]:
        """Load AI analysis prompts for different types of analysis"""
        return {
            'security_analysis': """
You are an expert AWS security analyst. Analyze these CloudTrail events for security threats and anomalies.

EVENTS: {events}
TIME_RANGE: {time_range}
TOTAL_EVENTS: {total_events}

ANALYZE FOR:
1. Security threats (unauthorized access, suspicious activity)
2. Anomalies (unusual patterns, off-hours activity)
3. Risk assessment (high, medium, low risk events)
4. Cost implications (expensive operations, resource creation)
5. Compliance issues (policy violations, audit concerns)

PROVIDE:
- Security risk score (0-100)
- Threat level (low/medium/high/critical)
- Key findings and concerns
- Recommended actions
- Cost impact assessment

Respond with JSON:
{{
    "security_risk_score": 75,
    "threat_level": "medium",
    "key_findings": ["..."],
    "concerns": ["..."],
    "recommended_actions": ["..."],
    "cost_impact": "high/medium/low",
    "anomalies_detected": true/false,
    "suspicious_events": ["..."],
    "compliance_issues": ["..."]
}}
""",    
            
            'anomaly_detection': """
You are an expert in detecting anomalies in AWS CloudTrail logs. Analyze these events for unusual patterns.

EVENTS: {events}
BASELINE_PATTERN: Normal activity includes {baseline_pattern}

DETECT:
1. Unusual access patterns
2. Off-hours activity
3. Unusual user behavior
4. Suspicious IP addresses
5. Unusual resource operations
6. Cost anomalies

ANALYZE:
- Frequency of events
- Time patterns
- User behavior changes
- Resource access patterns
- Cost implications

Respond with JSON:
{{
    "anomalies_detected": true/false,
    "anomaly_types": ["..."],
    "suspicious_events": ["..."],
    "confidence_score": 0.85,
    "risk_assessment": "low/medium/high",
    "recommendations": ["..."]
}}
""",
            
            'cost_analysis': """
You are an AWS cost optimization expert. Analyze these CloudTrail events for cost implications and optimization opportunities.

EVENTS: {events}
TIME_RANGE: {time_range}

ANALYZE:
1. High-cost operations
2. Resource creation patterns
3. Unused resource potential
4. Cost optimization opportunities
5. Budget impact

IDENTIFY:
- Expensive API calls
- Resource creation events
- Potential cost savings
- Budget risks
- Optimization recommendations

Respond with JSON:
{{
    "total_cost_impact": "high/medium/low",
    "high_cost_operations": ["..."],
    "resource_creation_events": ["..."],
    "cost_optimization_opportunities": ["..."],
    "budget_risks": ["..."],
    "recommended_actions": ["..."],
    "estimated_savings": "$X per month"
}}
""",
            
            'compliance_analysis': """
You are an AWS compliance and governance expert. Analyze these CloudTrail events for compliance issues and best practices.

EVENTS: {events}
COMPLIANCE_FRAMEWORKS: ["SOC2", "PCI-DSS", "HIPAA", "ISO27001"]

ANALYZE FOR:
1. Policy violations
2. Security best practice gaps
3. Compliance requirements
4. Audit trail completeness
5. Risk exposure

IDENTIFY:
- Compliance violations
- Security gaps
- Audit concerns
- Policy recommendations
- Risk mitigation steps

Respond with JSON:
{{
    "compliance_score": 85,
    "violations_detected": ["..."],
    "security_gaps": ["..."],
    "audit_concerns": ["..."],
    "policy_recommendations": ["..."],
    "risk_mitigation": ["..."],
    "overall_compliance": "compliant/partially_compliant/non-compliant"
}}
"""
        }
    
    async def analyze_security(self, events: List[Dict], time_range: Dict[str, str]) -> Dict[str, Any]:
        """Analyze CloudTrail events for security threats and risks"""
        try:
            if not events:
                return {
                    'success': False,
                    'error': 'No events to analyze'
                }
            
            # Prepare events for AI analysis
            events_summary = self._prepare_events_summary(events)
            
            # Create prompt for security analysis
            prompt = self.analysis_prompts['security_analysis'].format(
                events=events_summary,
                time_range=f"{time_range.get('start', 'unknown')} to {time_range.get('end', 'unknown')}",
                total_events=len(events)
            )
            
            # Get AI analysis
            ai_response = await self.groq_service.get_response(prompt)
            
            # Parse AI response
            try:
                analysis_result = json.loads(ai_response)
                analysis_result['success'] = True
                analysis_result['analysis_type'] = 'security'
                analysis_result['timestamp'] = datetime.utcnow().isoformat()
                return analysis_result
            except json.JSONDecodeError:
                # Fallback to text analysis if JSON parsing fails
                return {
                    'success': True,
                    'analysis_type': 'security',
                    'timestamp': datetime.utcnow().isoformat(),
                    'ai_response': ai_response,
                    'parsed': False
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze security: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def detect_anomalies(self, events: List[Dict], baseline_pattern: str = "normal business hours activity") -> Dict[str, Any]:
        """Detect anomalies in CloudTrail events"""
        try:
            if not events:
                return {
                    'success': False,
                    'error': 'No events to analyze'
                }
            
            # Prepare events for AI analysis
            events_summary = self._prepare_events_summary(events)
            
            # Create prompt for anomaly detection
            prompt = self.analysis_prompts['anomaly_detection'].format(
                events=events_summary,
                baseline_pattern=baseline_pattern
            )
            
            # Get AI analysis
            ai_response = await self.groq_service.get_response(prompt)
            
            # Parse AI response
            try:
                analysis_result = json.loads(ai_response)
                analysis_result['success'] = True
                analysis_result['analysis_type'] = 'anomaly_detection'
                analysis_result['timestamp'] = datetime.utcnow().isoformat()
                return analysis_result
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'analysis_type': 'anomaly_detection',
                    'timestamp': datetime.utcnow().isoformat(),
                    'ai_response': ai_response,
                    'parsed': False
                }
                
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_costs(self, events: List[Dict], time_range: Dict[str, str]) -> Dict[str, Any]:
        """Analyze CloudTrail events for cost implications"""
        try:
            if not events:
                return {
                    'success': False,
                    'error': 'No events to analyze'
                }
            
            # Prepare events for AI analysis
            events_summary = self._prepare_events_summary(events)
            
            # Create prompt for cost analysis
            prompt = self.analysis_prompts['cost_analysis'].format(
                events=events_summary,
                time_range=f"{time_range.get('start', 'unknown')} to {time_range.get('end', 'unknown')}"
            )
            
            # Get AI analysis
            ai_response = await self.groq_service.get_response(prompt)
            
            # Parse AI response
            try:
                analysis_result = json.loads(ai_response)
                analysis_result['success'] = True
                analysis_result['analysis_type'] = 'cost_analysis'
                analysis_result['timestamp'] = datetime.utcnow().isoformat()
                return analysis_result
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'analysis_type': 'cost_analysis',
                    'timestamp': datetime.utcnow().isoformat(),
                    'ai_response': ai_response,
                    'parsed': False
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze costs: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_compliance(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze CloudTrail events for compliance issues"""
        try:
            if not events:
                return {
                    'success': False,
                    'error': 'No events to analyze'
                }
            
            # Prepare events for AI analysis
            events_summary = self._prepare_events_summary(events)
            
            # Create prompt for compliance analysis
            prompt = self.analysis_prompts['compliance_analysis'].format(
                events=events_summary
            )
            
            # Get AI analysis
            ai_response = await self.groq_service.get_response(prompt)
            
            # Parse AI response
            try:
                analysis_result = json.loads(ai_response)
                analysis_result['success'] = True
                analysis_result['analysis_type'] = 'compliance_analysis'
                analysis_result['timestamp'] = datetime.utcnow().isoformat()
                return analysis_result
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'analysis_type': 'compliance_analysis',
                    'timestamp': datetime.utcnow().isoformat(),
                    'ai_response': ai_response,
                    'parsed': False
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze compliance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_events_summary(self, events: List[Dict]) -> str:
        """Prepare a summary of events for AI analysis"""
        if not events:
            return "No events to analyze"
        
        # Group events by type and create summary
        event_summary = []
        
        for event in events[:50]:  # Limit to first 50 events for AI analysis
            event_info = {
                'event_name': event.get('event_name', 'Unknown'),
                'event_source': event.get('event_source', 'Unknown'),
                'user_identity': event.get('user_identity', 'Unknown'),
                'source_ip': event.get('source_ip_address', 'Unknown'),
                'event_time': str(event.get('event_time', 'Unknown')),
                'risk_score': event.get('risk_score', 0.0),
                'suspicious': event.get('suspicious', False),
                'cost_impact': event.get('cost_impact', 0.0)
            }
            event_summary.append(event_info)
        
        return json.dumps(event_summary, indent=2)
    
    async def generate_security_report(self, events: List[Dict], time_range: Dict[str, str]) -> Dict[str, Any]:
        """Generate comprehensive security report from CloudTrail events"""
        try:
            # Run all analysis types
            security_analysis = await self.analyze_security(events, time_range)
            anomaly_detection = await self.detect_anomalies(events)
            cost_analysis = await self.analyze_costs(events, time_range)
            compliance_analysis = await self.analyze_compliance(events)
            
            # Compile comprehensive report
            report = {
                'success': True,
                'report_type': 'comprehensive_security',
                'timestamp': datetime.utcnow().isoformat(),
                'time_range': time_range,
                'total_events': len(events),
                'analysis_results': {
                    'security': security_analysis,
                    'anomalies': anomaly_detection,
                    'costs': cost_analysis,
                    'compliance': compliance_analysis
                },
                'executive_summary': self._generate_executive_summary(
                    security_analysis, anomaly_detection, cost_analysis, compliance_analysis
                ),
                'recommendations': self._compile_recommendations(
                    security_analysis, anomaly_detection, cost_analysis, compliance_analysis
                )
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_executive_summary(self, *analyses) -> str:
        """Generate executive summary from all analysis results"""
        summary_parts = []
        
        for analysis in analyses:
            if analysis.get('success') and analysis.get('parsed', True):
                analysis_type = analysis.get('analysis_type', 'unknown')
                
                if analysis_type == 'security':
                    risk_score = analysis.get('security_risk_score', 0)
                    threat_level = analysis.get('threat_level', 'unknown')
                    summary_parts.append(f"Security Risk: {risk_score}/100 ({threat_level} threat level)")
                
                elif analysis_type == 'anomaly_detection':
                    anomalies = analysis.get('anomalies_detected', False)
                    summary_parts.append(f"Anomalies: {'Detected' if anomalies else 'None detected'}")
                
                elif analysis_type == 'cost_analysis':
                    cost_impact = analysis.get('total_cost_impact', 'unknown')
                    summary_parts.append(f"Cost Impact: {cost_impact}")
                
                elif analysis_type == 'compliance_analysis':
                    compliance = analysis.get('overall_compliance', 'unknown')
                    summary_parts.append(f"Compliance: {compliance}")
        
        if summary_parts:
            return " | ".join(summary_parts)
        else:
            return "Analysis completed with limited insights due to parsing issues"
    
    def _compile_recommendations(self, *analyses) -> List[str]:
        """Compile recommendations from all analysis results"""
        recommendations = []
        
        for analysis in analyses:
            if analysis.get('success') and analysis.get('parsed', True):
                recs = analysis.get('recommended_actions', [])
                if isinstance(recs, list):
                    recommendations.extend(recs)
                elif isinstance(recs, str):
                    recommendations.append(recs)
        
        # Remove duplicates and return
        return list(set(recommendations))[:10]  # Limit to top 10 recommendations
