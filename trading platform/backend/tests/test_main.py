"""Tests for main application"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns correct response"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Trading Analytics Platform API"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


def test_health_check_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


def test_cors_headers(client):
    """Test that CORS headers are set correctly"""
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_openapi_docs_available(client):
    """Test that OpenAPI documentation is available"""
    response = client.get("/api/docs")
    assert response.status_code == 200
    
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "Trading Analytics Platform API"
