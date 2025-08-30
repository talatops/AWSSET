"""
WebSocket Router for Real-time Data Updates
Handles real-time AWS statistics and system status updates
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt
from sqlalchemy.orm import Session

from utils.auth import get_current_user
from utils.logger import get_aws_logger
from services.aws.stats_service import AWSStatsService
from services.aws.credential_manager import AWSCredentialManager
from database import get_db, User
from decouple import config

logger = get_aws_logger()
security = HTTPBearer()
router = APIRouter()

# WebSocket connection manager for real-time updates
class RealTimeConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_data: Dict[str, Dict] = {}
        self.update_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, user: User, db: Session):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_data[user_id] = {
            'user': user,
            'db': db,
            'last_aws_stats': None,
            'last_system_status': None
        }
        
        logger.info(f"🔌 Real-time WebSocket connected for user {user_id}")
        
        # Start periodic updates for this user
        self.update_tasks[user_id] = asyncio.create_task(
            self._periodic_updates(user_id)
        )
        
        # Send initial data
        await self._send_initial_data(user_id)
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            
        if user_id in self.user_data:
            del self.user_data[user_id]
            
        if user_id in self.update_tasks:
            self.update_tasks[user_id].cancel()
            del self.update_tasks[user_id]
            
        logger.info(f"🔌 Real-time WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: Dict, user_id: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending real-time message to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def _send_initial_data(self, user_id: str):
        """Send initial AWS stats and system status"""
        try:
            # Send AWS stats
            aws_stats = await self._get_aws_stats(user_id)
            if aws_stats:
                await self.send_personal_message({
                    'type': 'aws_stats_update',
                    'data': aws_stats,
                    'timestamp': datetime.utcnow().isoformat()
                }, user_id)
            
            # Send system status
            system_status = await self._get_system_status(user_id)
            await self.send_personal_message({
                'type': 'system_status_update',
                'data': system_status,
                'timestamp': datetime.utcnow().isoformat()
            }, user_id)
            
        except Exception as e:
            logger.error(f"Error sending initial data to {user_id}: {e}")
    
    async def _periodic_updates(self, user_id: str):
        """Send periodic updates every 30 seconds"""
        while user_id in self.active_connections:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                if user_id not in self.active_connections:
                    break
                
                # Get latest AWS stats
                aws_stats = await self._get_aws_stats(user_id)
                if aws_stats != self.user_data[user_id]['last_aws_stats']:
                    self.user_data[user_id]['last_aws_stats'] = aws_stats
                    await self.send_personal_message({
                        'type': 'aws_stats_update',
                        'data': aws_stats,
                        'timestamp': datetime.utcnow().isoformat()
                    }, user_id)
                
                # Get latest system status
                system_status = await self._get_system_status(user_id)
                if system_status != self.user_data[user_id]['last_system_status']:
                    self.user_data[user_id]['last_system_status'] = system_status
                    await self.send_personal_message({
                        'type': 'system_status_update',
                        'data': system_status,
                        'timestamp': datetime.utcnow().isoformat()
                    }, user_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic updates for {user_id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _get_aws_stats(self, user_id: str) -> Dict[str, Any]:
        """Get current AWS statistics for user"""
        try:
            user_data = self.user_data.get(user_id)
            if not user_data:
                return None
            
            user = user_data['user']
            
            # Get user's AWS credentials
            credential_manager = AWSCredentialManager()
            credentials = credential_manager.get_credentials(user_data['db'], user.id)
            
            if not credentials:
                return {
                    'success': False,
                    'error': 'No AWS credentials configured',
                    'services': {}
                }
            
            # Get AWS statistics
            stats_service = AWSStatsService(credentials)
            stats = await stats_service.get_all_service_stats()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting AWS stats for {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'services': {}
            }
    
    async def _get_system_status(self, user_id: str) -> Dict[str, Any]:
        """Get current system status"""
        try:
            # Check backend health
            backend_healthy = True  # Backend is running if we're here
            
            # Check chatbot service
            from services.ai.groq_service import groq_service
            chatbot_healthy = groq_service.is_configured
            
            # Check AWS credentials
            user_data = self.user_data.get(user_id)
            aws_healthy = False
            if user_data:
                credential_manager = AWSCredentialManager()
                credentials = credential_manager.get_credentials(user_data['db'], user_data['user'].id)
                aws_healthy = credentials is not None
            
            return {
                'backend': 'connected' if backend_healthy else 'disconnected',
                'chatbot': 'connected' if chatbot_healthy else 'disconnected',
                'aws': 'connected' if aws_healthy else 'disconnected'
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'backend': 'disconnected',
                'chatbot': 'disconnected',
                'aws': 'disconnected'
            }

# Global connection manager
real_time_manager = RealTimeConnectionManager()

async def get_user_from_token(token: str, db: Session) -> User:
    """Extract user from JWT token"""
    try:
        SECRET_KEY = config('JWT_SECRET_KEY', default='your-secret-key-here')
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        from sqlalchemy import and_
        user = db.query(User).filter(and_(User.id == int(user_id), User.is_active == True)).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID format")

@router.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time data updates
    """
    db = next(get_db())
    
    try:
        if not token:
            await websocket.close(code=1008, reason="Token required")
            return
        
        # Authenticate user
        user = await get_user_from_token(token, db)
        user_id = str(user.id)
        
        # Connect user
        await real_time_manager.connect(websocket, user_id, user, db)
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get('type')
                
                if message_type == 'request_aws_stats':
                    # Send immediate AWS stats update
                    aws_stats = await real_time_manager._get_aws_stats(user_id)
                    await real_time_manager.send_personal_message({
                        'type': 'aws_stats_update',
                        'data': aws_stats,
                        'timestamp': datetime.utcnow().isoformat()
                    }, user_id)
                
                elif message_type == 'request_system_status':
                    # Send immediate system status update
                    system_status = await real_time_manager._get_system_status(user_id)
                    await real_time_manager.send_personal_message({
                        'type': 'system_status_update',
                        'data': system_status,
                        'timestamp': datetime.utcnow().isoformat()
                    }, user_id)
                
                elif message_type == 'ping':
                    # Respond to ping
                    await real_time_manager.send_personal_message({
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    }, user_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    
    finally:
        if 'user_id' in locals():
            real_time_manager.disconnect(user_id)
