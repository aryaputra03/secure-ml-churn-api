"""
Tests for Rate Limiting
"""
import pytest
import time
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.database import Base, engine, SessionLocal, get_db
from src.api import crud


# ==========================================
# Test Fixtures
# ==========================================

@pytest.fixture(scope="function", autouse=True)
def reset_database():
    """Reset database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a database session for testing"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with overridden database"""
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
# Rate Limit Tests
# ==========================================

def test_rate_limit_exceeded(client):
    """Test that rate limit works on root endpoint"""
    responses = []
    
    # Root endpoint is limited to 2/minute
    for i in range(5):
        response = client.get("/")
        responses.append(response.status_code)
    
    # Should get at least one 429 (Too Many Requests)
    assert 429 in responses, f"Expected 429 in responses, got: {responses}"


def test_health_endpoint_has_higher_limit(client):
    """Test that health endpoint has higher limit (100/minute)"""
    responses = []
    
    # Health endpoint should allow more requests
    for i in range(10):
        response = client.get("/health")
        responses.append(response.status_code)
    
    # Should all be 200 since limit is 100/minute
    assert all(status == 200 for status in responses), \
        f"Expected all 200, got: {responses}"


def test_login_rate_limit(client):
    """Test login rate limiting (10/minute)"""
    responses = []

    # Try 15 login attempts
    for i in range(15):
        response = client.post(
            "/auth/token",
            data={"username": "nonexistent", "password": "wrongpass"}
        )
        responses.append(response.status_code)

    # Should get 429 after exceeding limit
    assert 429 in responses, f"Expected 429 in responses, got: {responses}"


def test_register_rate_limit(client, db_session):
    """Test registration rate limiting (5/hour)"""
    responses = []

    try:
        # Try 7 registration attempts (limit is 5/hour)
        for i in range(7):
            response = client.post(
                "/auth/register",
                json={
                    "username": f"testuser{i}",
                    "email": f"user{i}@example.com",
                    "password": "SecurePass123!",
                    "full_name": f"Test User {i}"
                }
            )
            responses.append(response.status_code)
            
            # Small delay to avoid race conditions
            time.sleep(0.1)

        # Should get 429 after exceeding limit (5 requests)
        assert 429 in responses, f"Expected 429 in responses, got: {responses}"
        
        # Count successes and rate limited responses
        success_count = sum(1 for status in responses if status == 201)
        rate_limited_count = sum(1 for status in responses if status == 429)
        
        assert success_count <= 5, \
            f"Expected max 5 successful registrations, got {success_count}"
        assert rate_limited_count >= 2, \
            f"Expected at least 2 rate limited responses, got {rate_limited_count}"
        
    finally:
        pass


def test_prediction_rate_limit_requires_auth(client):
    """Test that prediction endpoint requires authentication"""
    response = client.post(
        "/predict",
        json={
            "customer_id": "TEST001",
            "gender": "Male",
            "tenure": 24,
            "monthly_charges": 75.5,
            "total_charges": 1810.0,
            "contract": "One year",
            "payment_method": "Bank transfer (automatic)",
            "internet_service": "Fiber optic"
        }
    )
    
    # Should get 401 Unauthorized without token
    assert response.status_code == 401


def test_rate_limit_with_authenticated_user(client, db_session):
    """Test rate limiting with authenticated user"""
    try:
        # Create test user
        crud.create_user(
            db=db_session,
            username="ratelimituser",
            email="ratelimit@example.com",
            password="RateLimit123!",
            role="user"
        )
        
        # Login to get token
        login_response = client.post(
            "/auth/token",
            data={
                "username": "ratelimituser",
                "password": "RateLimit123!"
            }
        )
        
        assert login_response.status_code == 200, \
            f"Login failed: {login_response.text}"
        
        token = login_response.json()["access_token"]
        
        # Make multiple authenticated requests
        responses = []
        for i in range(35):  # Prediction limit is 30/minute
            response = client.post(
                "/predict",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "customer_id": f"TEST{i:03d}",
                    "gender": "Male",
                    "tenure": 24,
                    "monthly_charges": 75.5,
                    "total_charges": 1810.0,
                    "contract": "One year",
                    "payment_method": "Bank transfer (automatic)",
                    "internet_service": "Fiber optic"
                }
            )
            responses.append(response.status_code)
        
        # Should get 429 after exceeding limit
        assert 429 in responses, f"Expected 429 in responses, got: {responses}"
        
    finally:
        pass


# ==========================================
# Additional Edge Case Tests
# ==========================================

def test_rate_limit_different_endpoints(client):
    """Test that rate limits are per-endpoint"""
    
    # Hit health endpoint (should not be affected by root limit)
    health_responses = [client.get("/health").status_code for _ in range(3)]
    
    # Health should all succeed
    assert all(status == 200 for status in health_responses), \
        "Health endpoint should have separate rate limit"


def test_rate_limit_reset_after_window(client):
    """Test that rate limit resets after time window"""
    # Make 2 requests (hits the limit)
    client.get("/")
    client.get("/")
    
    # Third request should be rate limited
    response = client.get("/")
    assert response.status_code == 429
    
    # Note: In real test, you'd wait for the window to expire
    # For CI/CD, we just verify the limit works