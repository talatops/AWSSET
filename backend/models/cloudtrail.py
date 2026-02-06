"""
CloudTrail Event Models
Stores CloudTrail events and AI analysis results
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from datetime import datetime
from database import Base

class CloudTrailEvent(Base):
    """CloudTrail event model for storing security logs"""
    __tablename__ = "cloudtrail_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_name = Column(String, nullable=False, index=True)
    event_source = Column(String, nullable=False, index=True)
    event_time = Column(DateTime, nullable=False, index=True)
    user_identity = Column(JSON, nullable=True)
    aws_region = Column(String, nullable=True)
    source_ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    request_parameters = Column(JSON, nullable=True)
    response_elements = Column(JSON, nullable=True)
    additional_event_data = Column(JSON, nullable=True)
    api_version = Column(String, nullable=True)
    read_only = Column(Boolean, default=False)
    management_event = Column(Boolean, default=True)
    insight_details = Column(JSON, nullable=True)
    
    # AI Analysis Results
    ai_analysis = Column(JSON, nullable=True)
    risk_score = Column(Float, default=0.0)
    anomaly_detected = Column(Boolean, default=False)
    security_incident = Column(Boolean, default=False)
    cost_impact = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CloudTrailEvent(id={self.id}, event_name='{self.event_name}', event_time='{self.event_time}')>"

class SecurityIncident(Base):
    """Security incident model for tracking security events"""
    __tablename__ = "security_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, nullable=False, index=True)  # low, medium, high, critical
    status = Column(String, default="open", index=True)  # open, investigating, resolved, false_positive
    incident_type = Column(String, nullable=False, index=True)  # unauthorized_access, cost_spike, anomaly, etc.
    
    # Related CloudTrail events
    related_events = Column(JSON, nullable=True)  # List of event IDs
    
    # AI Analysis
    ai_analysis = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0.0)
    recommended_actions = Column(JSON, nullable=True)
    
    # Cost impact
    estimated_cost_impact = Column(Float, default=0.0)
    actual_cost_impact = Column(Float, default=0.0)
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SecurityIncident(id={self.id}, title='{self.title}', severity='{self.severity}')>"

class AnomalyDetection(Base):
    """Anomaly detection model for storing detected anomalies"""
    __tablename__ = "anomaly_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    anomaly_id = Column(String, unique=True, index=True, nullable=False)
    anomaly_type = Column(String, nullable=False, index=True)  # cost, access, performance, etc.
    description = Column(Text, nullable=True)
    severity = Column(String, nullable=False, index=True)  # low, medium, high, critical
    
    # Detection details
    baseline_metrics = Column(JSON, nullable=True)
    current_metrics = Column(JSON, nullable=True)
    deviation_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    
    # Related data
    related_events = Column(JSON, nullable=True)
    affected_resources = Column(JSON, nullable=True)
    
    # AI Analysis
    ai_analysis = Column(JSON, nullable=True)
    recommended_actions = Column(JSON, nullable=True)
    
    # Status
    status = Column(String, default="detected", index=True)  # detected, investigating, resolved, false_positive
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AnomalyDetection(id={self.id}, type='{self.anomaly_type}', severity='{self.severity}')>"

class SecurityInsight(Base):
    """Security insights model for storing AI-generated security insights"""
    __tablename__ = "security_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    insight_type = Column(String, nullable=False, index=True)  # threat, cost, performance, compliance
    category = Column(String, nullable=False, index=True)  # security, cost_optimization, performance, etc.
    
    # AI Analysis
    ai_generated = Column(Boolean, default=True)
    confidence_score = Column(Float, default=0.0)
    risk_level = Column(String, nullable=False, index=True)  # low, medium, high, critical
    
    # Related data
    related_events = Column(JSON, nullable=True)
    affected_resources = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    
    # Recommendations
    recommendations = Column(JSON, nullable=True)
    action_items = Column(JSON, nullable=True)
    
    # Status
    status = Column(String, default="active", index=True)  # active, dismissed, implemented
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SecurityInsight(id={self.id}, title='{self.title}', type='{self.insight_type}')>"
