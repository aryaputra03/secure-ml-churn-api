"""
Pytest Configuration and Fixtures

Common fixtures for testing the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.database import Base, get_db
from src.api import crud

# ==========================================
# Test Database Setup
# ==========================================

# Use in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==========================================
# Database Fixtures
# ==========================================

@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """
    Create test client with test database
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

# ==========================================
# User Fixtures
# ==========================================

@pytest.fixture
def test_user(db_session):
    """
    Create a test user
    """
    user = crud.create_user(
        db=db_session,
        username="testuser",
        email="test@example.com",
        password="TestPass123!",
        role="user"
    )
    return user

@pytest.fixture
def test_admin(db_session):
    """
    Create a test admin user
    """
    admin = crud.create_user(
        db=db_session,
        username="adminuser",
        email="admin@example.com",
        password="AdminPass123!",
        role="admin"
    )
    return admin

@pytest.fixture
def auth_token(client, test_user):
    """
    Get authentication token for test user
    """
    response = client.post(
        "/auth/token",
        data={
            "username": "testuser",
            "password": "TestPass123!"
        }
    )
    
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture
def admin_token(client, test_admin):
    """
    Get authentication token for admin user
    """
    response = client.post(
        "/auth/token",
        data={
            "username": "adminuser",
            "password": "AdminPass123!"
        }
    )
    
    assert response.status_code == 200
    return response.json()["access_token"]

# ==========================================
# Environment Configuration
# ==========================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """
    Setup test environment variables
    """
    import os
    
    # Set test environment variables
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["TESTING"] = "true"
    
    # Use in-memory rate limiting for tests
    if "REDIS_URL" in os.environ:
        del os.environ["REDIS_URL"]
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

# ==========================================
# Rate Limiting Reset
# ==========================================

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """
    Reset rate limiter before each test
    """
    from src.api.rate_limit import rate_limiter
    
    # Reset in-memory rate limiter
    if hasattr(rate_limiter, 'requests'):
        rate_limiter.requests.clear()
    
    # Reset slowapi limiter
    try:
        from src.api.main import limiter
        limiter.reset()
    except Exception:
        pass
    
    yield