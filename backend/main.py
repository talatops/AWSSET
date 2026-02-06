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
from routers import auth, aws_services, aws_credentials, ec2, aws_stats, chat, websocket, cloudtrail, s3, lambda_routes, rds, cost_management
from database import engine, Base
from middleware.security import SecurityMiddleware
from utils.logger import setup_logger
from utils.config import AppConfig, validate_configuration

# Setup logging
logger = setup_logger(__name__)

# Validate configuration on startup (fails fast if critical settings like JWT_SECRET_KEY are missing)
validate_configuration()

# NOTE: Database schema should be managed via Alembic migrations in production.
# Base.metadata.create_all(bind=engine)

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

# CORS middleware - environment-driven configuration
allowed_origins = AppConfig.CORS_ORIGINS
logger.info(f"Configuring CORS with allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(s3.router, prefix="/api/aws/s3", tags=["S3"])
app.include_router(lambda_routes.router, prefix="/api/aws/lambda", tags=["Lambda"])
app.include_router(rds.router, prefix="/api/aws/rds", tags=["RDS"])
app.include_router(aws_stats.router, prefix="/api/aws", tags=["AWS Statistics"])
app.include_router(aws_services.router, prefix="/api/aws", tags=["AWS Services"])
app.include_router(cost_management.router, prefix="/api/cost", tags=["Cost Management"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(cloudtrail.router, tags=["CloudTrail"])

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
    """Health check endpoint for monitoring"""
    from database import test_db_connection
    import redis
    
    health_status = {
        "status": "healthy",
        "service": "aws-chatbot-backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database health check
    try:
        db_healthy = test_db_connection()
        health_status["checks"]["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Redis health check
    try:
        redis_client = redis.from_url(AppConfig.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unavailable: {str(e)}"
        health_status["status"] = "degraded"
    
    # Overall status
    if any("error" in str(check) or "unhealthy" in str(check) for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status


@app.get("/api/metrics")
async def get_metrics():
    """Metrics endpoint for monitoring (Prometheus-compatible)"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    metrics = {
        "cpu_percent": process.cpu_percent(interval=0.1),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "memory_percent": process.memory_percent(),
        "threads": process.num_threads(),
        "open_files": len(process.open_files()),
        "connections": len(process.connections()),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return metrics

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
