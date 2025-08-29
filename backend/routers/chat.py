"""
Chat API Router for AWS Chatbot
Handles real-time chat interactions and AWS command execution
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
import json

from utils.auth import get_current_user
from utils.logger import get_aws_logger
from services.ai.gemini_service import groq_service
from services.aws.credential_manager import AWSCredentialManager
from services.aws.ec2_service import EC2Service
from database import get_db, User
from sqlalchemy.orm import Session

logger = get_aws_logger()
security = HTTPBearer()

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Pydantic Models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")

class ChatResponse(BaseModel):
    response: Dict[str, Any]
    message_id: str
    timestamp: str
    conversation_id: Optional[str] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"🔌 WebSocket connected for user {user_id}")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"🔌 WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: Dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending WebSocket message to {user_id}: {e}")
                self.disconnect(user_id)

manager = ConnectionManager()

async def format_aws_command_response(ai_response: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format AWS command execution results into human-readable responses
    """
    try:
        service = ai_response.get('service')
        action = ai_response.get('action')
        
        if service == 'ec2' and action == 'list':
            # Format EC2 instances list
            instances = execution_result.get('data', [])
            count = execution_result.get('count', 0)
            
            if count == 0:
                formatted_message = "🔍 **No EC2 instances found**\n\nYou don't have any EC2 instances in your account yet. Would you like me to help you launch one?"
            else:
                formatted_message = f"🖥️ **Found {count} EC2 Instance{'s' if count != 1 else ''}**\n\n"
                
                for instance in instances:
                    state_emoji = {
                        'running': '🟢',
                        'stopped': '🔴', 
                        'pending': '🟡',
                        'stopping': '🟡',
                        'terminated': '⚫',
                        'terminating': '🟡'
                    }.get(instance.get('state', ''), '⚪')
                    
                    formatted_message += f"{state_emoji} **{instance.get('name') or instance.get('instance_id')}**\n"
                    formatted_message += f"   • **Type:** {instance.get('instance_type')}\n"
                    formatted_message += f"   • **State:** {instance.get('state').title()}\n"
                    formatted_message += f"   • **ID:** {instance.get('instance_id')}\n"
                    
                    if instance.get('public_ip'):
                        formatted_message += f"   • **Public IP:** {instance.get('public_ip')}\n"
                    if instance.get('private_ip'):
                        formatted_message += f"   • **Private IP:** {instance.get('private_ip')}\n"
                    if instance.get('key_name'):
                        formatted_message += f"   • **Key Pair:** {instance.get('key_name')}\n"
                    
                    formatted_message += "\n"
                
                formatted_message += "💡 **Need help?** Ask me to start, stop, or terminate any instance!"
            
            ai_response['message'] = formatted_message
            ai_response['type'] = 'aws_command_success'
            
        elif service == 'ec2' and action == 'create':
            # Format EC2 instance creation
            result_data = execution_result.get('data', {})
            instances = result_data.get('instances', [])
            
            if instances:
                instance = instances[0]
                formatted_message = f"🚀 **EC2 Instance Launched Successfully!**\n\n"
                formatted_message += f"✅ **Instance Created:**\n"
                formatted_message += f"   • **ID:** {instance.get('instance_id')}\n"
                formatted_message += f"   • **Type:** {instance.get('instance_type')}\n"
                formatted_message += f"   • **State:** {instance.get('state').title()}\n"
                formatted_message += f"   • **AMI:** {instance.get('image_id')}\n"
                
                if instance.get('name'):
                    formatted_message += f"   • **Name:** {instance.get('name')}\n"
                if instance.get('key_name'):
                    formatted_message += f"   • **Key Pair:** {instance.get('key_name')}\n"
                
                formatted_message += f"\n🕐 **Note:** Instance is starting up and will be available shortly.\n"
                formatted_message += f"💰 **Billing:** Charges apply while instance is running.\n"
                formatted_message += f"\n🎯 **Next Steps:** You can start, stop, or connect to this instance once it's running!"
            else:
                formatted_message = "❌ **Instance launch failed.** Please check your configuration and try again."
            
            ai_response['message'] = formatted_message
            ai_response['type'] = 'aws_command_success'
            
        elif service == 'ec2' and action in ['start', 'stop', 'reboot', 'terminate']:
            # Format EC2 instance state change
            result_data = execution_result.get('data', {})
            instance_id = result_data.get('instance_id', 'Unknown')
            current_state = result_data.get('current_state', 'Unknown')
            previous_state = result_data.get('previous_state', 'Unknown')
            
            action_emoji = {
                'start': '▶️',
                'stop': '⏹️', 
                'reboot': '🔄',
                'terminate': '🗑️'
            }.get(action, '⚙️')
            
            action_past = {
                'start': 'started',
                'stop': 'stopped',
                'reboot': 'rebooted', 
                'terminate': 'terminated'
            }.get(action, f'{action}ed')
            
            formatted_message = f"{action_emoji} **EC2 Instance {action_past.title()}**\n\n"
            formatted_message += f"✅ **Operation Successful:**\n"
            formatted_message += f"   • **Instance ID:** {instance_id}\n"
            formatted_message += f"   • **Previous State:** {previous_state.title()}\n"
            formatted_message += f"   • **Current State:** {current_state.title()}\n"
            
            if action == 'terminate':
                formatted_message += f"\n⚠️ **Warning:** This instance will be permanently deleted.\n"
                formatted_message += f"💰 **Billing:** Charges will stop once termination is complete.\n"
            elif action == 'stop':
                formatted_message += f"\n💰 **Billing:** Instance charges stopped. EBS storage charges continue.\n"
            elif action == 'start':
                formatted_message += f"\n💰 **Billing:** Instance charges resumed.\n"
            
            formatted_message += f"\n🕐 **Note:** State changes may take a few moments to complete."
            
            ai_response['message'] = formatted_message
            ai_response['type'] = 'aws_command_success'
            
        # Keep the execution result for reference but hide the raw data
        ai_response['formatted'] = True
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error formatting AWS response: {str(e)}")
        # Fallback to original response
        return ai_response

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the AI chatbot and get response
    """
    try:
        user_id = str(current_user.id)
        message_id = f"msg_{int(datetime.utcnow().timestamp() * 1000)}"
        
        logger.info(f"💬 Processing chat message from user {user_id}: {chat_message.message[:100]}...")
        
        # Process message with AI service
        ai_response = await groq_service.process_message(
            message=chat_message.message,
            user_id=user_id,
            conversation_id=chat_message.conversation_id
        )
        
        # If it's an AWS command, execute it
        if ai_response.get('type') == 'aws_command' and ai_response.get('requires_execution'):
            execution_result = await execute_aws_command(ai_response, current_user)
            ai_response['execution_result'] = execution_result
            
            # Format the response for better user experience
            if execution_result.get('success'):
                ai_response = await format_aws_command_response(ai_response, execution_result)
        
        # Create response
        response = ChatResponse(
            response=ai_response,
            message_id=message_id,
            timestamp=datetime.utcnow().isoformat(),
            conversation_id=chat_message.conversation_id
        )
        
        # Send via WebSocket if connected
        await manager.send_personal_message({
            'type': 'chat_response',
            'data': response.dict()
        }, user_id)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/health")
async def chat_health_check():
    """Health check for chat service"""
    return {
        "status": "healthy",
        "ai_service_configured": groq_service.is_configured,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/suggestions")
async def get_chat_suggestions(current_user: User = Depends(get_current_user)):
    """
    Get suggested messages/commands for the user
    """
    try:
        suggestions = [
            {
                'category': 'EC2 Management',
                'suggestions': [
                    'Show me my EC2 instances',
                    'Launch a new t2.micro instance',
                    'Stop all running instances'
                ]
            },
            {
                'category': 'AWS Knowledge',
                'suggestions': [
                    'What is AWS Lambda?',
                    'Explain EC2 instance types',
                    'AWS cost optimization tips'
                ]
            }
        ]
        
        return {
            'suggestions': suggestions,
            'user_id': str(current_user.id)
        }
        
    except Exception as e:
        logger.error(f"Error getting chat suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving suggestions")

@router.get("/health")
async def chat_health_check():
    """
    Health check for chat service
    """
    return {
        'status': 'healthy',
        'ai_service_configured': groq_service.is_configured,
        'websocket_connections': len(manager.active_connections),
        'timestamp': datetime.utcnow().isoformat()
    }

# Helper function to execute AWS commands
async def execute_aws_command(ai_response: Dict[str, Any], current_user: User) -> Dict[str, Any]:
    """
    Execute AWS commands based on AI interpretation
    """
    try:
        service = ai_response.get('service')
        action = ai_response.get('action')
        parameters = ai_response.get('parameters', {})
        
        logger.info(f"🚀 Executing AWS command: {service}.{action}")
        
        # Get AWS credentials for user
        user_id = str(current_user.id)
        credential_manager = AWSCredentialManager()
        
        # Get database session to retrieve real credentials
        db = next(get_db())
        credentials = credential_manager.get_credentials(db, int(user_id))
        
        if not credentials:
            return {
                'success': False,
                'error': 'AWS credentials not found. Please configure your AWS credentials first.',
                'requires_setup': True
            }
        
        # Execute based on service
        if service == 'ec2':
            return await execute_ec2_command(action, parameters, int(user_id), db)
        else:
            return {
                'success': False,
                'error': f'Service {service} is not yet supported',
                'supported_services': ['ec2']
            }
    
    except Exception as e:
        logger.error(f"Error executing AWS command: {str(e)}")
        return {
            'success': False,
            'error': f'Error executing command: {str(e)}'
        }

async def execute_ec2_command(action: str, parameters: Dict, user_id: int, db: Session) -> Dict[str, Any]:
    """
    Execute EC2-specific commands
    """
    try:
        ec2_service = EC2Service(db, user_id)
        
        if action == 'list':
            instances_result = ec2_service.list_instances()
            if instances_result.get('success'):
                instances = instances_result.get('instances', [])
                return {
                    'success': True,
                    'action': 'list_instances',
                    'data': instances,
                    'count': len(instances),
                    'message': f'Found {len(instances)} EC2 instances'
                }
            else:
                return instances_result
        
        elif action in ['create', 'launch']:
            instance_type = parameters.get('instance_type', 't2.micro')
            ami_id = 'ami-0c02fb55956c7d316'  # Amazon Linux 2 AMI
            
            instance_config = {
                'ImageId': ami_id,
                'InstanceType': instance_type,
                'MinCount': 1,
                'MaxCount': 1
            }
            
            if parameters.get('key_name'):
                instance_config['KeyName'] = parameters['key_name']
            if parameters.get('security_groups'):
                instance_config['SecurityGroupIds'] = parameters['security_groups']
            if parameters.get('subnet_id'):
                instance_config['SubnetId'] = parameters['subnet_id']
            if parameters.get('name'):
                instance_config['Name'] = parameters['name']
            
            result = ec2_service.create_instance(instance_config)
            
            if result.get('success'):
                return {
                    'success': True,
                    'action': 'create_instance',
                    'data': result,
                    'message': f'Successfully launched {instance_type} instance'
                }
            else:
                return result
        
        elif action == 'start':
            instance_id = parameters.get('instance_id')
            if not instance_id:
                return {
                    'success': False,
                    'error': 'Instance ID is required for start operation'
                }
            
            result = ec2_service.start_instance(instance_id)
            
            if result.get('success'):
                return {
                    'success': True,
                    'action': 'start_instance',
                    'data': {
                        'instance_id': instance_id,
                        'current_state': result.get('current_state'),
                        'previous_state': result.get('previous_state')
                    },
                    'message': f'Successfully started instance {instance_id}'
                }
            else:
                return result
        
        elif action == 'stop':
            instance_id = parameters.get('instance_id')
            force = parameters.get('force', False)
            if not instance_id:
                return {
                    'success': False,
                    'error': 'Instance ID is required for stop operation'
                }
            
            result = ec2_service.stop_instance(instance_id, force=force)
            
            if result.get('success'):
                return {
                    'success': True,
                    'action': 'stop_instance',
                    'data': {
                        'instance_id': instance_id,
                        'current_state': result.get('current_state'),
                        'previous_state': result.get('previous_state')
                    },
                    'message': f'Successfully stopped instance {instance_id}'
                }
            else:
                return result
        
        elif action == 'reboot':
            instance_id = parameters.get('instance_id')
            if not instance_id:
                return {
                    'success': False,
                    'error': 'Instance ID is required for reboot operation'
                }
            
            result = ec2_service.reboot_instance(instance_id)
            
            if result.get('success'):
                return {
                    'success': True,
                    'action': 'reboot_instance',
                    'data': {
                        'instance_id': instance_id,
                        'current_state': result.get('current_state'),
                        'previous_state': result.get('previous_state')
                    },
                    'message': f'Successfully rebooted instance {instance_id}'
                }
            else:
                return result
        
        elif action == 'terminate':
            instance_id = parameters.get('instance_id')
            if not instance_id:
                return {
                    'success': False,
                    'error': 'Instance ID is required for terminate operation'
                }
            
            result = ec2_service.terminate_instance(instance_id)
            
            if result.get('success'):
                return {
                    'success': True,
                    'action': 'terminate_instance',
                    'data': {
                        'instance_id': instance_id,
                        'current_state': result.get('current_state'),
                        'previous_state': result.get('previous_state')
                    },
                    'message': f'Successfully terminated instance {instance_id}'
                }
            else:
                return result
        
        else:
            return {
                'success': False,
                'error': f'EC2 action "{action}" is not yet supported',
                'supported_actions': ['list', 'create', 'launch', 'start', 'stop', 'reboot', 'terminate']
            }
    
    except Exception as e:
        logger.error(f"Error executing EC2 command: {str(e)}")
        return {
            'success': False,
            'error': f'EC2 command failed: {str(e)}'
        }