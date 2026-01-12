"""
Tests for Rate Limiting
"""
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.database import Base, engine, SessionLocal
from src.api import crud
import pytest
import time

# Reset database before tests
@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

def test_rate_limit_exceeded(client):
    """Test that rate limit works on root endpoint"""
    responses = []
    
    # Root endpoint is limited to 2/minute in your code
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
    assert all(status == 200 for status in responses), f"Expected all 200, got: {responses}"

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

def test_register_rate_limit(client):
    """Test registration rate limiting (5/hour)"""
    responses = []
    db = SessionLocal()

    try:
        # Try 7 registration attempts (limit is 5/hour)
        for i in range(7):
            response = client.post(
                "/auth/register",
                json={
                    "username": f"testuser{i}",
                    "email": f"user{i}@example.com",
                    "password": "SecurePass123!",  # Valid password
                    "full_name": f"Test User {i}"
                }
            )
            responses.append(response.status_code)
            
            # Small delay to avoid race conditions
            time.sleep(0.1)

        # Print responses for debugging
        print(f"Registration responses: {responses}")
        
        # Should get 429 after exceeding limit (5 requests)
        assert 429 in responses, f"Expected 429 in responses, got: {responses}"
        
        # First 5 should succeed (201), rest should be rate limited (429)
        success_count = sum(1 for status in responses if status == 201)
        rate_limited_count = sum(1 for status in responses if status == 429)
        
        assert success_count <= 5, f"Expected max 5 successful registrations, got {success_count}"
        assert rate_limited_count >= 2, f"Expected at least 2 rate limited responses, got {rate_limited_count}"
        
    finally:
        db.close()

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

def test_rate_limit_with_authenticated_user(client):
    """Test rate limiting with authenticated user"""
    db = SessionLocal()
    
    try:
        # Create test user
        crud.create_user(
            db=db,
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
        
        assert login_response.status_code == 200
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
        db.close()