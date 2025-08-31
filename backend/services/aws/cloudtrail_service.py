"""
CloudTrail Service
Handles CloudTrail event fetching, processing, and analysis
"""

import boto3    
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, NoCredentialsError
from datetime import datetime, timedelta
import json
import logging

from .aws_client import AWSBaseClient
from utils.logger import get_aws_logger

logger = get_aws_logger()

class CloudTrailService(AWSBaseClient):
    """Service for CloudTrail operations and analysis"""
    
    def __init__(self, db, user_id):
        super().__init__(db, user_id, 'cloudtrail')
        self.cloudtrail_client = self.client
        self.logs_client = boto3.client('logs', **self._get_credentials())
    
    def _get_credentials(self) -> Dict[str, str]:
        """Get AWS credentials for the service"""
        from .credential_manager import AWSCredentialManager
        credential_manager = AWSCredentialManager()
        return credential_manager.get_credentials(self.db, self.user_id)
    
    async def get_trail_status(self) -> Dict[str, Any]:
        """Get CloudTrail trail status and configuration"""
        try:
            trails_response = self.cloudtrail_client.describe_trails()
            trails = trails_response.get('trailList', [])
            
            if not trails:
                return {
                    'success': False,
                    'message': 'No CloudTrail trails found',
                    'trails': []
                }
            
            trail_statuses = []
            for trail in trails:
                try:
                    status = self.cloudtrail_client.get_trail_status(
                        Name=trail['Name']
                    )
                    trail_statuses.append({
                        'name': trail['Name'],
                        'status': status,
                        'configuration': trail
                    })
                except Exception as e:
                    logger.warning(f"Failed to get status for trail {trail['Name']}: {e}")
                    trail_statuses.append({
                        'name': trail['Name'],
                        'status': {'error': str(e)},
                        'configuration': trail
                    })
            
            return {
                'success': True,
                'trails': trail_statuses,
                'total_trails': len(trails)
            }
            
        except Exception as e:
            logger.error(f"Failed to get CloudTrail status: {e}")
            return {
                'success': False,
                'error': str(e),
                'trails': []
            }
    
    async def fetch_events(self, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          event_names: Optional[List[str]] = None,
                          user_identities: Optional[List[str]] = None,
                          source_ips: Optional[List[str]] = None,
                          read_only: Optional[bool] = None,
                          management_event: Optional[bool] = None,
                          max_results: int = 50) -> Dict[str, Any]:
        """Fetch CloudTrail events with filtering"""
        try:
            # Default to last 24 hours if no time specified
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.utcnow()
            
            # Prepare lookup parameters
            lookup_params = {
                'StartTime': start_time,
                'EndTime': end_time,
                'MaxResults': min(max_results, 50)  # CloudTrail max is 50
            }
            
            if event_names:
                lookup_params['EventName'] = event_names
            
            # Fetch events
            response = self.cloudtrail_client.lookup_events(**lookup_params)
            events = response.get('Events', [])
            
            # Process and enrich events
            processed_events = []
            for event in events:
                processed_event = self._process_event(event)
                processed_events.append(processed_event)
            
            # Apply additional filters
            if user_identities or source_ips or read_only is not None or management_event is not None:
                processed_events = self._apply_filters(
                    processed_events, 
                    user_identities, 
                    source_ips, 
                    read_only, 
                    management_event
                )
            
            return {
                'success': True,
                'events': processed_events,
                'total_events': len(processed_events),
                'next_token': response.get('NextToken'),
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch CloudTrail events: {e}")
            return {
                'success': False,
                'error': str(e),
                'events': []
            }
    
    def _process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enrich a CloudTrail event"""
        try:
            # Extract key information
            processed_event = {
                'event_id': event.get('EventId'),
                'event_name': event.get('EventName'),
                'event_source': event.get('EventSource'),
                'event_time': event.get('EventTime'),
                'user_identity': event.get('Username'),
                'aws_region': event.get('AwsRegion'),
                'source_ip_address': event.get('SourceIPAddress'),
                'user_agent': event.get('UserAgent'),
                'request_parameters': event.get('RequestParameters'),
                'response_elements': event.get('ResponseElements'),
                'additional_event_data': event.get('AdditionalEventData'),
                'api_version': event.get('ApiVersion'),
                'read_only': event.get('ReadOnly', False),
                'management_event': event.get('ManagementEvent', True),
                'insight_details': event.get('InsightDetails'),
                'raw_event': event  # Keep original for reference
            }
            
            # Calculate risk score based on event characteristics
            processed_event['risk_score'] = self._calculate_risk_score(event)
            
            # Determine if event is suspicious
            processed_event['suspicious'] = self._is_suspicious_event(event)
            
            # Extract cost impact if available
            processed_event['cost_impact'] = self._extract_cost_impact(event)
            
            return processed_event
            
        except Exception as e:
            logger.error(f"Failed to process event {event.get('EventId')}: {e}")
            return {
                'event_id': event.get('EventId'),
                'error': str(e),
                'raw_event': event
            }
    
    def _calculate_risk_score(self, event: Dict[str, Any]) -> float:
        """Calculate risk score for an event (0.0 to 1.0)"""
        risk_score = 0.0
        
        # High-risk event names
        high_risk_events = [
            'DeleteBucket', 'DeleteInstance', 'DeleteSecurityGroup',
            'DeleteRole', 'DeleteUser', 'DeletePolicy', 'DeleteTrail',
            'StopLogging', 'PutUserPolicy', 'AttachRolePolicy'
        ]
        
        # Medium-risk event names
        medium_risk_events = [
            'CreateInstance', 'CreateSecurityGroup', 'CreateUser',
            'CreateRole', 'CreatePolicy', 'ModifySecurityGroup',
            'ModifyInstanceAttribute', 'ModifyUser', 'ModifyRole'
        ]
        
        event_name = event.get('EventName', '')
        
        # Base risk based on event type
        if event_name in high_risk_events:
            risk_score += 0.6
        elif event_name in medium_risk_events:
            risk_score += 0.3
        
        # Risk based on source IP (external IPs are higher risk)
        source_ip = event.get('SourceIPAddress', '')
        if source_ip and not self._is_internal_ip(source_ip):
            risk_score += 0.2
        
        # Risk based on user identity (root user is higher risk)
        username = event.get('Username', '')
        if username and 'root' in username.lower():
            risk_score += 0.3
        
        # Risk based on time (off-hours are higher risk)
        event_time = event.get('EventTime')
        if event_time:
            hour = event_time.hour
            if hour < 6 or hour > 22:  # Off-hours
                risk_score += 0.1
        
        # Risk based on read-only vs write operations
        if not event.get('ReadOnly', True):
            risk_score += 0.2
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    def _is_suspicious_event(self, event: Dict[str, Any]) -> bool:
        """Determine if an event is suspicious"""
        # High risk score indicates suspicious activity
        risk_score = self._calculate_risk_score(event)
        return risk_score > 0.7
    
    def _is_internal_ip(self, ip: str) -> bool:
        """Check if IP is internal/private"""
        if not ip:
            return False
        
        # Simple check for private IP ranges
        private_ranges = [
            '10.', '192.168.', '172.16.', '172.17.', '172.18.',
            '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
            '172.29.', '172.30.', '172.31.'
        ]
        
        return any(ip.startswith(prefix) for prefix in private_ranges)
    
    def _extract_cost_impact(self, event: Dict[str, Any]) -> float:
        """Extract potential cost impact from an event"""
        cost_impact = 0.0
        
        event_name = event.get('EventName', '')
        
        # High-cost operations
        if event_name in ['RunInstances', 'CreateVolume', 'CreateSnapshot']:
            cost_impact += 10.0  # Base cost for resource creation
        
        # Medium-cost operations
        elif event_name in ['ModifyInstanceAttribute', 'ModifyVolume']:
            cost_impact += 5.0
        
        # Low-cost operations
        elif event_name in ['StartInstances', 'StopInstances']:
            cost_impact += 1.0
        
        return cost_impact

    def _apply_filters(self, events: List[Dict[str, Any]], 
                       user_identities: Optional[List[str]] = None,
                       source_ips: Optional[List[str]] = None,
                       read_only: Optional[bool] = None,
                       management_event: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Apply additional filters to processed events"""
        try:
            filtered_events = events
            
            # Filter by user identities
            if user_identities:
                filtered_events = [
                    event for event in filtered_events
                    if event.get('user_identity') and 
                    any(identity.lower() in event['user_identity'].lower() for identity in user_identities)
                ]
            
            # Filter by source IPs
            if source_ips:
                filtered_events = [
                    event for event in filtered_events
                    if event.get('source_ip_address') and 
                    any(ip in event['source_ip_address'] for ip in source_ips)
                ]
            
            # Filter by read-only status
            if read_only is not None:
                filtered_events = [
                    event for event in filtered_events
                    if event.get('read_only') == read_only
                ]
            
            # Filter by management event status
            if management_event is not None:
                filtered_events = [
                    event for event in filtered_events
                    if event.get('management_event') == management_event
                ]
            
            return filtered_events
            
        except Exception as e:
            logger.error(f"Failed to apply filters: {e}")
            return events  # Return original events if filtering fails
    
    async def get_event_statistics(self, 
                                  start_time: Optional[datetime] = None,
                                  end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics about CloudTrail events"""
        try:
            # Fetch events for analysis
            events_response = await self.fetch_events(start_time, end_time, max_results=1000)
            
            if not events_response['success']:
                return events_response
            
            events = events_response['events']
            
            # Calculate statistics
            stats = {
                'total_events': len(events),
                'event_types': {},
                'risk_distribution': {'low': 0, 'medium': 0, 'high': 0},
                'suspicious_events': 0,
                'cost_impact': 0.0,
                'top_users': {},
                'top_source_ips': {},
                'top_event_sources': {}
            }
            
            for event in events:
                # Event type distribution
                event_name = event.get('event_name', 'Unknown')
                stats['event_types'][event_name] = stats['event_types'].get(event_name, 0) + 1
                
                # Risk distribution
                risk_score = event.get('risk_score', 0.0)
                if risk_score < 0.3:
                    stats['risk_distribution']['low'] += 1
                elif risk_score < 0.7:
                    stats['risk_distribution']['medium'] += 1
                else:
                    stats['risk_distribution']['high'] += 1
                
                # Suspicious events
                if event.get('suspicious', False):
                    stats['suspicious_events'] += 1
                
                # Cost impact
                stats['cost_impact'] += event.get('cost_impact', 0.0)
                
                # Top users
                username = event.get('user_identity', 'Unknown')
                stats['top_users'][username] = stats['top_users'].get(username, 0) + 1
                
                # Top source IPs
                source_ip = event.get('source_ip_address', 'Unknown')
                stats['top_source_ips'][source_ip] = stats['top_source_ips'].get(source_ip, 0) + 1
                
                # Top event sources
                event_source = event.get('event_source', 'Unknown')
                stats['top_event_sources'][event_source] = stats['top_event_sources'].get(event_source, 0) + 1
            
            # Sort top lists
            stats['top_users'] = dict(sorted(stats['top_users'].items(), key=lambda x: x[1], reverse=True)[:10])
            stats['top_source_ips'] = dict(sorted(stats['top_source_ips'].items(), key=lambda x: x[1], reverse=True)[:10])
            stats['top_event_sources'] = dict(sorted(stats['top_event_sources'].items(), key=lambda x: x[1], reverse=True)[:10])
            
            return {
                'success': True,
                'statistics': stats,
                'time_range': events_response.get('time_range')
            }
            
        except Exception as e:
            logger.error(f"Failed to get event statistics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def search_events(self, 
                           query: str,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           max_results: int = 50) -> Dict[str, Any]:
        """Search CloudTrail events using natural language query"""
        try:
            # Parse query to extract search parameters
            search_params = self._parse_search_query(query)
            
            # Fetch events with search filters
            events_response = await self.fetch_events(
                start_time=start_time or search_params.get('start_time'),
                end_time=end_time or search_params.get('end_time'),
                event_names=search_params.get('event_names'),
                max_results=max_results
            )
            
            if not events_response['success']:
                return events_response
            
            events = events_response['events']
            
            # Apply additional search filters
            if search_params.get('keywords'):
                filtered_events = []
                keywords = search_params['keywords'].lower().split()
                
                for event in events:
                    event_text = json.dumps(event).lower()
                    if all(keyword in event_text for keyword in keywords):
                        filtered_events.append(event)
                
                events = filtered_events
            
            return {
                'success': True,
                'events': events,
                'total_events': len(events),
                'search_query': query,
                'search_params': search_params
            }
            
        except Exception as e:
            logger.error(f"Failed to search events: {e}")
            return {
                'success': False,
                'error': str(e),
                'events': []
            }
    
    def _parse_search_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language search query into search parameters"""
        query_lower = query.lower()
        search_params = {}
        
        # Extract time references
        if 'today' in query_lower:
            search_params['start_time'] = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'yesterday' in query_lower:
            search_params['start_time'] = (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'last week' in query_lower:
            search_params['start_time'] = datetime.utcnow() - timedelta(weeks=1)
        elif 'last month' in query_lower:
            search_params['start_time'] = datetime.utcnow() - timedelta(days=30)
        
        # Extract event types
        event_keywords = {
            'delete': ['Delete', 'Terminate', 'Remove'],
            'create': ['Create', 'Launch', 'Start'],
            'modify': ['Modify', 'Update', 'Change'],
            'access': ['Get', 'List', 'Describe', 'View']
        }
        
        for keyword, event_types in event_keywords.items():
            if keyword in query_lower:
                search_params['event_names'] = event_types
                break
        
        # Extract keywords for text search
        search_params['keywords'] = query
        
        return search_params
