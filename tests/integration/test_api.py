"""
Integration tests for API endpoints.
"""
import os
import pytest
import requests
import time
import json
from typing import Dict, Any

# API URL from environment or default
API_URL = os.environ.get("TEST_API_URL", "http://localhost:8000")

# Test credentials
TEST_USERNAME = os.environ.get("TEST_USERNAME", "test_user")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "test_password")

# Test document paths
TEST_PDF = os.path.join(os.path.dirname(__file__), "../data/test.pdf")
TEST_TEXT = os.path.join(os.path.dirname(__file__), "../data/test.txt")


@pytest.fixture(scope="session")
def auth_token() -> str:
    """Get authentication token for API requests."""
    response = requests.post(
        f"{API_URL}/auth/token",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


def test_health_endpoint():
    """Test health endpoint."""
    response = requests.get(f"{API_URL}/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_api_version():
    """Test API version endpoint."""
    response = requests.get(f"{API_URL}/version")
    
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "api_version" in data


def test_upload_document(auth_headers: Dict[str, str]):
    """Test document upload."""
    # Skip if test file doesn't exist
    if not os.path.exists(TEST_PDF):
        pytest.skip(f"Test file not found: {TEST_PDF}")
    
    with open(TEST_PDF, "rb") as f:
        files = {"file": (os.path.basename(TEST_PDF), f, "application/pdf")}
        response = requests.post(
            f"{API_URL}/documents/upload",
            files=files,
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "success"
    
    # Return document ID for later tests
    return data["document_id"]


def test_document_processing(auth_headers: Dict[str, str]):
    """Test document processing."""
    # First upload a document
    document_id = test_upload_document(auth_headers)
    
    # Wait for processing to start
    time.sleep(1)
    
    # Check processing status
    max_attempts = 10
    for i in range(max_attempts):
        response = requests.get(
            f"{API_URL}/documents/{document_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If processing is complete, break
        if data["processing_status"] in ["ready", "error"]:
            break
        
        # Wait before next check
        time.sleep(2)
    
    # Final status check
    assert data["processing_status"] in ["ready", "error"]
    
    # If error, print error message
    if data["processing_status"] == "error" and "metadata" in data and "error" in data["metadata"]:
        print(f"Processing error: {data['metadata']['error']}")
    
    return document_id


def test_search(auth_headers: Dict[str, str]):
    """Test search functionality."""
    # Search query
    query = "test"
    
    response = requests.get(
        f"{API_URL}/search",
        params={"query": query, "k": 5},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    
    # Results may be empty if no documents match
    if data["results"]:
        assert "content" in data["results"][0]
        assert "score" in data["results"][0]
        assert "document_id" in data["results"][0]


def test_document_version(auth_headers: Dict[str, str]):
    """Test document versioning."""
    # First upload a document
    document_id = test_upload_document(auth_headers)
    
    # Create a new version
    content = "This is a new version of the document."
    response = requests.post(
        f"{API_URL}/documents/{document_id}/versions",
        json={"content": content},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert data["status"] in ["success", "unchanged"]
    
    # Get version
    response = requests.get(
        f"{API_URL}/documents/{document_id}/versions/{data['version']}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    version_data = response.json()
    assert "content" in version_data
    
    # Compare with original
    response = requests.get(
        f"{API_URL}/documents/{document_id}/versions/compare",
        params={"version1": 1, "version2": data["version"]},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    compare_data = response.json()
    assert "diff" in compare_data


def test_metrics(auth_headers: Dict[str, str]):
    """Test metrics endpoint."""
    response = requests.get(
        f"{API_URL}/metrics/stats",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "queries" in data
    assert "documents" in data
    assert "chunks" in data
    assert "feedback" in data


if __name__ == "__main__":
    # Create pytest arguments
    pytest_args = ["-xvs", __file__]
    
    # Run tests
    pytest.main(pytest_args)