"""
AWS Chatbot Backend - Main Application Entry Point
FastAPI application with WebSocket support for real-time chat
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from decouple import config
import logging
from datetime import datetime

# Import custom modules
from routers import auth, aws_services, aws_credentials, ec2, aws_stats, chat, websocket
from database import engine, Base
from middleware.security import SecurityMiddleware
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AWS Chatbot API",
    description="AI-powered AWS management chatbot backend",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security
security = HTTPBearer()

# CORS middleware - permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom security middleware
app.add_middleware(SecurityMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(aws_credentials.router, prefix="/api/aws", tags=["AWS Credentials"])
app.include_router(ec2.router, prefix="/api/aws/ec2", tags=["EC2 Instances"])
app.include_router(aws_stats.router, prefix="/api/aws", tags=["AWS Statistics"])
app.include_router(aws_services.router, prefix="/api/aws", tags=["AWS Services"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(websocket.router, tags=["WebSocket"])

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "service": "AWS Chatbot API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "message": "AWS Chatbot API is running!",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "aws-chatbot-backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(config("PORT", default=8000))
    host = config("HOST", default="0.0.0.0")
    
    logger.info(f"Starting AWS Chatbot Backend on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
