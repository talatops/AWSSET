"""
Cost Optimization Service
Provides budget monitoring, cost optimization recommendations, and unused resource detection
"""

import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from utils.logger import get_aws_logger
from .aws_client import AWSBaseClient

logger = get_aws_logger()


class CostOptimizationService(AWSBaseClient):
    """Service for cost optimization and budget monitoring"""
    
    def __init__(self, db, user_id):
        super().__init__(db, user_id, "ce")  # Cost Explorer
        self.budgets_client = self.session.client('budgets') if self.session else None
    
    async def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status and alerts"""
        try:
            if not self.budgets_client:
                return {
                    "success": False,
                    "error": "Budgets API not available",
                    "note": "AWS Budgets requires additional permissions"
                }
            
            response = self.budgets_client.describe_budgets(AccountId=self._get_account_id())
            
            budgets = []
            for budget in response.get('Budgets', []):
                budget_data = {
                    "budget_name": budget['BudgetName'],
                    "budget_limit": budget.get('BudgetLimit', {}).get('Amount', '0'),
                    "time_unit": budget.get('TimeUnit', 'MONTHLY'),
                    "budget_type": budget.get('BudgetType', 'COST'),
                    "calculated_spend": budget.get('CalculatedSpend', {}),
                    "time_period": budget.get('TimePeriod', {}),
                    "cost_filters": budget.get('CostFilters', {}),
                }
                budgets.append(budget_data)
            
            return {
                "success": True,
                "budgets": budgets,
                "count": len(budgets),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get budget status: {e}")
            return {
                "success": False,
                "error": str(e),
                "note": "Budget monitoring requires AWS Budgets API access"
            }
    
    async def detect_unused_resources(self) -> Dict[str, Any]:
        """Detect unused or underutilized AWS resources"""
        try:
            unused_resources = []
            
            # Check for stopped EC2 instances older than 7 days
            ec2_client = self.session.client('ec2')
            response = ec2_client.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]
            )
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    launch_time = instance.get('LaunchTime')
                    if launch_time:
                        days_stopped = (datetime.utcnow() - launch_time.replace(tzinfo=None)).days
                        if days_stopped > 7:
                            unused_resources.append({
                                "resource_type": "EC2",
                                "resource_id": instance['InstanceId'],
                                "resource_name": self._get_instance_name(instance),
                                "status": "stopped",
                                "days_inactive": days_stopped,
                                "estimated_monthly_cost": self._estimate_ec2_cost(instance),
                                "recommendation": "Consider terminating if not needed"
                            })
            
            # Check for unattached EBS volumes
            volumes_response = ec2_client.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )
            
            for volume in volumes_response.get('Volumes', []):
                create_time = volume.get('CreateTime')
                if create_time:
                    days_unattached = (datetime.utcnow() - create_time.replace(tzinfo=None)).days
                    if days_unattached > 7:
                        unused_resources.append({
                            "resource_type": "EBS Volume",
                            "resource_id": volume['VolumeId'],
                            "status": "unattached",
                            "days_inactive": days_unattached,
                            "size_gb": volume.get('Size', 0),
                            "estimated_monthly_cost": self._estimate_ebs_cost(volume),
                            "recommendation": "Consider deleting if not needed"
                        })
            
            # Check for empty S3 buckets
            s3_client = self.session.client('s3')
            buckets_response = s3_client.list_buckets()
            
            for bucket in buckets_response.get('Buckets', []):
                try:
                    objects_response = s3_client.list_objects_v2(Bucket=bucket['Name'], MaxKeys=1)
                    if 'Contents' not in objects_response:
                        # Empty bucket
                        unused_resources.append({
                            "resource_type": "S3 Bucket",
                            "resource_id": bucket['Name'],
                            "status": "empty",
                            "days_inactive": (datetime.utcnow() - bucket['CreationDate'].replace(tzinfo=None)).days,
                            "estimated_monthly_cost": 0.0,
                            "recommendation": "Consider deleting if not needed"
                        })
                except Exception:
                    pass
            
            total_potential_savings = sum(r.get('estimated_monthly_cost', 0) for r in unused_resources)
            
            return {
                "success": True,
                "unused_resources": unused_resources,
                "count": len(unused_resources),
                "total_potential_savings": round(total_potential_savings, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to detect unused resources: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_cost_optimization_recommendations(self) -> Dict[str, Any]:
        """Get AI-powered cost optimization recommendations"""
        try:
            recommendations = []
            
            # Get current costs
            ce_client = self.client
            now = datetime.utcnow()
            start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            
            try:
                cost_response = ce_client.get_cost_and_usage(
                    TimePeriod={'Start': start_date, 'End': end_date},
                    Granularity='MONTHLY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
                )
                
                # Analyze costs and generate recommendations
                for result in cost_response.get('ResultsByTime', []):
                    for group in result.get('Groups', []):
                        service = group['Keys'][0]
                        cost = float(group['Metrics']['UnblendedCost']['Amount'])
                        
                        if cost > 100:  # Focus on services costing more than $100/month
                            recommendations.append({
                                "service": service,
                                "current_monthly_cost": cost,
                                "recommendations": self._generate_service_recommendations(service, cost)
                            })
            except Exception as e:
                logger.warning(f"Cost Explorer API not available: {e}")
                recommendations.append({
                    "service": "General",
                    "recommendations": [
                        "Enable AWS Cost Explorer for detailed cost analysis",
                        "Set up AWS Budgets to monitor spending",
                        "Review and terminate unused resources regularly",
                        "Use Reserved Instances for predictable workloads",
                        "Enable S3 lifecycle policies to move old data to cheaper storage"
                    ]
                })
            
            return {
                "success": True,
                "recommendations": recommendations,
                "count": len(recommendations),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimization recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts_client = self.session.client('sts')
            return sts_client.get_caller_identity()['Account']
        except Exception:
            return "unknown"
    
    def _get_instance_name(self, instance: Dict) -> str:
        """Extract instance name from tags"""
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                return tag['Value']
        return instance['InstanceId']
    
    def _estimate_ec2_cost(self, instance: Dict) -> float:
        """Estimate monthly EC2 cost (simplified)"""
        # This is a simplified estimation - actual costs vary by region and instance type
        instance_type = instance.get('InstanceType', 't2.micro')
        # Rough estimates (these should be fetched from AWS Pricing API in production)
        cost_per_hour = {
            't2.micro': 0.0116,
            't2.small': 0.023,
            't2.medium': 0.0464,
            't3.micro': 0.0104,
            'm5.large': 0.096,
        }.get(instance_type, 0.05)
        
        return round(cost_per_hour * 24 * 30, 2)
    
    def _estimate_ebs_cost(self, volume: Dict) -> float:
        """Estimate monthly EBS cost"""
        size_gb = volume.get('Size', 0)
        volume_type = volume.get('VolumeType', 'gp2')
        # Rough estimates
        cost_per_gb = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
        }.get(volume_type, 0.10)
        
        return round(size_gb * cost_per_gb, 2)
    
    def _generate_service_recommendations(self, service: str, cost: float) -> List[str]:
        """Generate service-specific recommendations"""
        recommendations = []
        
        if 'EC2' in service:
            recommendations.extend([
                "Consider using Reserved Instances for predictable workloads",
                "Review instance sizes - rightsize if over-provisioned",
                "Use Spot Instances for fault-tolerant workloads",
                "Schedule instances to stop during non-business hours"
            ])
        
        if 'S3' in service:
            recommendations.extend([
                "Enable S3 Intelligent-Tiering for automatic cost optimization",
                "Set up lifecycle policies to move old data to Glacier",
                "Review and delete unused buckets",
                "Enable S3 versioning only where necessary"
            ])
        
        if 'RDS' in service:
            recommendations.extend([
                "Consider Reserved Instances for production databases",
                "Review database instance sizes",
                "Enable automated backups only for critical databases",
                "Consider Aurora Serverless for variable workloads"
            ])
        
        if 'Lambda' in service:
            recommendations.extend([
                "Optimize function memory allocation",
                "Review and optimize function execution time",
                "Use provisioned concurrency only when needed",
                "Consider Step Functions for complex workflows"
            ])
        
        return recommendations
