"""
AWS Lambda Service Implementation
Lambda function management functionality
"""

import boto3
from typing import Dict, List, Any, Optional
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session
from datetime import datetime
from utils.logger import get_aws_logger
from .aws_client import AWSBaseClient
from database import AWSResource

logger = get_aws_logger()


class LambdaService(AWSBaseClient):
    """Lambda service implementation for function management"""
    
    def __init__(self, db: Session, user_id: int):
        super().__init__(db, user_id, "lambda")
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def list_functions(self) -> Dict[str, Any]:
        """List all Lambda functions"""
        try:
            paginator = self.client.get_paginator('list_functions')
            functions = []
            
            for page in paginator.paginate():
                for func in page.get('Functions', []):
                    function_data = {
                        "function_name": func['FunctionName'],
                        "function_arn": func['FunctionArn'],
                        "runtime": func.get('Runtime', ''),
                        "handler": func.get('Handler', ''),
                        "code_size": func.get('CodeSize', 0),
                        "description": func.get('Description', ''),
                        "timeout": func.get('Timeout', 0),
                        "memory_size": func.get('MemorySize', 0),
                        "last_modified": func.get('LastModified', '').isoformat() if func.get('LastModified') else None,
                        "state": func.get('State', 'Active'),
                        "state_reason": func.get('StateReason', '')
                    }
                    functions.append(function_data)
                    
                    # Track in database
                    self._track_aws_resource(
                        resource_type='lambda',
                        resource_id=func['FunctionName'],
                        resource_name=func['FunctionName'],
                        resource_arn=func['FunctionArn'],
                        status=func.get('State', 'Active'),
                        meta_data=function_data
                    )
            
            result = {
                "success": True,
                "functions": functions,
                "count": len(functions),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("list_functions", {"count": len(functions)})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "list_functions")
    
    def get_function(self, function_name: str) -> Dict[str, Any]:
        """Get detailed information about a Lambda function"""
        try:
            response = self.client.get_function(FunctionName=function_name)
            
            configuration = response['Configuration']
            function_data = {
                "function_name": configuration['FunctionName'],
                "function_arn": configuration['FunctionArn'],
                "runtime": configuration.get('Runtime', ''),
                "handler": configuration.get('Handler', ''),
                "code_size": configuration.get('CodeSize', 0),
                "description": configuration.get('Description', ''),
                "timeout": configuration.get('Timeout', 0),
                "memory_size": configuration.get('MemorySize', 0),
                "role": configuration.get('Role', ''),
                "environment": configuration.get('Environment', {}).get('Variables', {}),
                "last_modified": configuration.get('LastModified', '').isoformat() if configuration.get('LastModified') else None,
                "state": configuration.get('State', 'Active')
            }
            
            result = {
                "success": True,
                "function": function_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "get_function", {"function_name": function_name})
    
    def invoke_function(self, function_name: str, payload: Optional[Dict] = None, 
                       invocation_type: str = 'RequestResponse') -> Dict[str, Any]:
        """Invoke a Lambda function"""
        try:
            import json
            
            invoke_params = {
                'FunctionName': function_name,
                'InvocationType': invocation_type
            }
            
            if payload:
                invoke_params['Payload'] = json.dumps(payload)
            
            response = self.client.invoke(**invoke_params)
            
            result_payload = {}
            if 'Payload' in response:
                result_payload = json.loads(response['Payload'].read())
            
            result = {
                "success": True,
                "function_name": function_name,
                "status_code": response.get('StatusCode', 200),
                "payload": result_payload,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._log_operation("invoke_function", {"function_name": function_name})
            return result
            
        except Exception as e:
            return self._handle_aws_error(e, "invoke_function", {"function_name": function_name})
    
    def get_function_metrics(self, function_name: str) -> Dict[str, Any]:
        """Get CloudWatch metrics for a Lambda function"""
        try:
            cloudwatch = self.session.client('cloudwatch')
            
            end_time = datetime.utcnow()
            start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            metrics = {}
            
            # Get invocation count
            invocations = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            metrics['invocations'] = sum(point['Sum'] for point in invocations.get('Datapoints', []))
            
            # Get errors
            errors = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            metrics['errors'] = sum(point['Sum'] for point in errors.get('Datapoints', []))
            
            # Get duration
            duration = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            metrics['avg_duration_ms'] = sum(point['Average'] for point in duration.get('Datapoints', [])) / max(len(duration.get('Datapoints', [])), 1)
            
            result = {
                "success": True,
                "function_name": function_name,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to get Lambda metrics: {e}")
            return {
                "success": False,
                "error": str(e),
                "function_name": function_name
            }
