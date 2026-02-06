"""
Pytest configuration and fixtures for backend tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from unittest.mock import Mock, patch

# Import before database setup
from database import Base, get_db
from main import app
from utils.config import AppConfig

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for tests"""
    with patch('routers.auth.redis_client') as mock_redis_client:
        yield mock_redis_client


@pytest.fixture(scope="function")
def mock_aws_client():
    """Mock AWS boto3 client"""
    with patch('boto3.client') as mock_client:
        yield mock_client


@pytest.fixture(scope="function")
def mock_groq_client():
    """Mock Groq AI client"""
    with patch('services.ai.gemini_service.groq') as mock_groq:
        yield mock_groq


@pytest.fixture(scope="function")
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture(scope="function")
def sample_aws_credentials():
    """Sample AWS credentials for testing"""
    return {
        "access_key": "AKIAIOSFODNN7EXAMPLE",
        "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region": "us-east-1"
    }


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')
    # Reload config after env changes
    from importlib import reload
    import utils.config
    reload(utils.config)
