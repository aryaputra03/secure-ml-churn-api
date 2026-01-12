"""
Tests for Rate Limiting
"""
from fastapi.testclient import TestClient
from src.api.main import app
import time

client = TestClient(app)

def test_rate_limit_exceeded():
    """Test that rate limit works"""
    responses = []
    for i in range(70):
        response = client.get("/")
        responses.append(response.status_code)
    
    assert 429 in responses

def test_limit_reset():
    """Test that rate limit resets"""
    response1 = client.get("/")
    assert response1.status_code == 200
    time.sleep(61)
    response2 = client.get("/")
    assert response2.status_code == 200

def test_login_rate_limit():
    """Test login rate limiting"""
    responses = []

    for i in range(15):
        response = client.post(
            "/auth/token",
            data={"username": "test", "password": "test"}
        )
        responses.append(response.status_code)

    assert 429 in responses

def test_register_rate_limit():
    """Test registration rate limiting"""
    responses = []

    for i in range(7):
        response = client.post(
            "/auth/register",
            json={
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": "Pass123!"
            }
        )
        responses.append(response.status_code)

    assert 429 in responses

