import boto3
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from botocore.exceptions import ClientError, NoCredentialsError
from utils.logger import get_aws_logger

logger = get_aws_logger()

class AWSBillingService:
    """Service for fetching AWS billing and cost information"""
    
    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        self.credentials = credentials
        self.region = credentials.get('region_name', 'us-east-1') if credentials else 'us-east-1'
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        if credentials:
            self.session = boto3.Session(**credentials)
    
    def _get_client(self, service_name: str):
        """Get a client for the specified service"""
        if not self.session:
            raise ValueError("No AWS session available")
        return self.session.client(service_name)
    
    async def get_current_month_costs(self) -> Dict[str, Any]:
        """
        Get current month costs for all AWS services
        """
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_costs():
                try:
                    # Use Cost Explorer API
                    ce_client = self._get_client('ce')
                    
                    # Calculate date range for current month
                    now = datetime.utcnow()
                    start_date = now.replace(day=1).strftime('%Y-%m-%d')
                    end_date = now.strftime('%Y-%m-%d')
                    
                    # Get costs by service
                    response = ce_client.get_cost_and_usage(
                        TimePeriod={
                            'Start': start_date,
                            'End': end_date
                        },
                        Granularity='MONTHLY',
                        Metrics=['UnblendedCost'],
                        GroupBy=[
                            {
                                'Type': 'DIMENSION',
                                'Key': 'SERVICE'
                            }
                        ]
                    )
                    
                    # Parse the response
                    costs_by_service = {}
                    total_cost = 0.0
                    
                    for result in response['ResultsByTime']:
                        for group in result['Groups']:
                            service_name = group['Keys'][0]
                            cost = float(group['Metrics']['UnblendedCost']['Amount'])
                            costs_by_service[service_name] = cost
                            total_cost += cost
                    
                    # Get estimated monthly cost (extrapolate from current month)
                    days_in_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - now.replace(day=1)
                    days_elapsed = now.day
                    estimated_monthly = (total_cost / days_elapsed) * days_in_month.days if days_elapsed > 0 else total_cost
                    
                    return {
                        'success': True,
                        'current_month': total_cost,
                        'estimated_monthly': estimated_monthly,
                        'by_service': costs_by_service,
                        'period': f"{start_date} to {end_date}",
                        'currency': 'USD'
                    }
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AccessDenied':
                        logger.warning("Access denied to Cost Explorer API. User may not have billing permissions.")
                        return self._get_fallback_costs()
                    else:
                        raise e
                        
            return await loop.run_in_executor(self.executor, fetch_costs)
            
        except Exception as e:
            logger.error(f"Failed to fetch AWS costs: {e}")
            return self._get_fallback_costs()
    
    def _get_fallback_costs(self) -> Dict[str, Any]:
        """
        Fallback costs when Cost Explorer is not accessible
        """
        return {
            'success': False,
            'current_month': 0.0,
            'estimated_monthly': 0.0,
            'by_service': {},
            'period': 'Current month',
            'currency': 'USD',
            'note': 'Cost Explorer API access required for real-time billing data'
        }
    
    async def get_service_costs(self, service_names: list) -> Dict[str, Any]:
        """
        Get costs for specific services
        """
        try:
            costs = await self.get_current_month_costs()
            
            if not costs['success']:
                return costs
            
            service_costs = {}
            for service in service_names:
                # Map service names to AWS service names
                aws_service_name = self._map_service_name(service)
                cost = costs['by_service'].get(aws_service_name, 0.0)
                service_costs[service] = cost
            
            return {
                'success': True,
                'service_costs': service_costs,
                'total': sum(service_costs.values()),
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Failed to get service costs: {e}")
            return {
                'success': False,
                'service_costs': {},
                'total': 0.0,
                'currency': 'USD'
            }
    
    def _map_service_name(self, service_name: str) -> str:
        """
        Map our service names to AWS service names
        """
        mapping = {
            'ec2': 'Amazon Elastic Compute Cloud - Compute',
            's3': 'Amazon Simple Storage Service',
            'lambda': 'AWS Lambda',
            'rds': 'Amazon Relational Database Service',
            'iam': 'AWS Identity and Access Management',
            'bedrock': 'Amazon Bedrock'
        }
        return mapping.get(service_name.lower(), service_name)
    
    async def get_daily_costs(self, days: int = 7) -> Dict[str, Any]:
        """
        Get daily costs for the last N days
        """
        try:
            loop = asyncio.get_event_loop()
            
            def fetch_daily_costs():
                try:
                    ce_client = self._get_client('ce')
                    
                    # Calculate date range
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=days)
                    
                    response = ce_client.get_cost_and_usage(
                        TimePeriod={
                            'Start': start_date.strftime('%Y-%m-%d'),
                            'End': end_date.strftime('%Y-%m-%d')
                        },
                        Granularity='DAILY',
                        Metrics=['UnblendedCost']
                    )
                    
                    daily_costs = []
                    for result in response['ResultsByTime']:
                        date = result['TimePeriod']['Start']
                        cost = float(result['Total']['UnblendedCost']['Amount'])
                        daily_costs.append({
                            'date': date,
                            'cost': cost
                        })
                    
                    return {
                        'success': True,
                        'daily_costs': daily_costs,
                        'total': sum(day['cost'] for day in daily_costs),
                        'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                    }
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AccessDenied':
                        logger.warning("Access denied to Cost Explorer API for daily costs")
                        return {'success': False, 'daily_costs': [], 'total': 0.0}
                    else:
                        raise e
            
            return await loop.run_in_executor(self.executor, fetch_daily_costs)
            
        except Exception as e:
            logger.error(f"Failed to fetch daily costs: {e}")
            return {'success': False, 'daily_costs': [], 'total': 0.0}
