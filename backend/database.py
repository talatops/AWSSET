"""
Database configuration and models for AWS Chatbot
SQLAlchemy setup with PostgreSQL
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from decouple import config
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = config("DATABASE_URL", default="postgresql://awschatbot:secure_password@localhost:5432/awschatbot_db")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=config("DEBUG", default=False, cast=bool)
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database Models
class User(Base):
    """User model for authentication and session management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # For local auth
    provider = Column(String, nullable=False, default="local")  # google, proton, local
    provider_id = Column(String, nullable=True)  # OAuth provider ID
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    profile_customized = Column(Boolean, default=False)  # Track if user has edited their profile
    aws_access_key = Column(String, nullable=True)  # Encrypted
    aws_secret_key = Column(String, nullable=True)  # Encrypted
    aws_region = Column(String, default="us-east-1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatSession(Base):
    """Chat session model for storing conversation history"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ChatMessage(Base):
    """Chat message model for storing individual messages"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    message_type = Column(String, nullable=False)  # user, bot, system, error
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)  # Store additional context
    aws_service = Column(String, nullable=True)  # Which AWS service was involved
    operation_type = Column(String, nullable=True)  # create, read, update, delete
    operation_status = Column(String, nullable=True)  # success, error, pending
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class AWSResource(Base):
    """AWS resource tracking model"""
    __tablename__ = "aws_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    resource_type = Column(String, nullable=False)  # ec2, s3, lambda, etc.
    resource_id = Column(String, nullable=False)  # AWS resource ID
    resource_name = Column(String, nullable=True)
    resource_arn = Column(String, nullable=True)
    region = Column(String, nullable=False)
    status = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)  # Store resource-specific data
    created_via_chat = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SystemLog(Base):
    """System logging model for audit trails"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    level = Column(String, nullable=False)  # info, warning, error, critical
    service = Column(String, nullable=False)  # aws_service, auth, system
    operation = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# Dependency to get database session
def get_db() -> Session:
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database initialization
def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

# Test database connection
def test_db_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
