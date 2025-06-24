"""
Tests for the Agent Management API endpoints.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.router.main import app
from services.router.cams_client import CAMSClient

# Create a test client using the FastAPI app with dependency overrides
@pytest.fixture
def test_client(mock_cams_client):
    def override_get_cams_client():
        return mock_cams_client
        
    app.dependency_overrides[get_cams_client] = override_get_cams_client
    
    with TestClient(app) as client:
        yield client
    
    # Clean up after test
    app.dependency_overrides.clear()

# Test data
TEST_AGENT_ADDRESS = "test-agent@example.com"
TEST_AGENT_MAPPING = {
    "ai_agent_address": TEST_AGENT_ADDRESS,
    "inbox_destination_type": "GCP_PUBSUB_TOPIC",
    "inbox_name": "projects/test/topics/test-agent-inbox",
    "status": "ACTIVE",
    "registration_timestamp": "2025-01-01T00:00:00Z",
    "last_updated_timestamp": "2025-01-01T00:00:00Z",
    "updated_by": "test",
}

# Fixtures
@pytest.fixture
def mock_cams_client():
    with patch('services.router.cams_client.CAMSClient') as MockCAMSClient:
        mock_instance = AsyncMock()
        MockCAMSClient.return_value = mock_instance
        yield mock_instance
        
# Import after defining the fixture to avoid circular imports
from services.router.routers.agent_management import get_cams_client

# Test cases
class TestAgentManagementAPI:
    def test_register_agent_mapping_success(self, test_client, mock_cams_client):
        """Test successful agent registration."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=None)
        mock_cams_client.register_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        
        # Test data
        agent_data = {
            "ai_agent_address": TEST_AGENT_ADDRESS,
            "inbox_destination_type": "GCP_PUBSUB_TOPIC",
            "inbox_name": "projects/test/topics/test-agent-inbox",
            "description": "Test agent",
            "owner_team": "test-team"
        }
        
        # Make request
        response = test_client.post("/v1/agent-inboxes", json=agent_data)
        
        # Assertions
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["ai_agent_address"] == TEST_AGENT_ADDRESS
        assert response_data["status"] == "ACTIVE"
        
        # Verify CAMS client was called correctly
        mock_cams_client.get_agent_mapping.assert_awaited_once_with(TEST_AGENT_ADDRESS)
        
        # Get the actual call arguments
        mock_cams_client.register_agent_mapping.assert_awaited_once()
        args, kwargs = mock_cams_client.register_agent_mapping.await_args
        
        # Verify required fields
        assert kwargs['ai_agent_address'] == TEST_AGENT_ADDRESS
        assert kwargs['inbox_destination_type'] == "GCP_PUBSUB_TOPIC"
        assert kwargs['inbox_name'] == "projects/test/topics/test-agent-inbox"
        assert kwargs['description'] == "Test agent"
        assert kwargs['status'] == "ACTIVE"
        assert kwargs['updated_by'] == "agent_management_api"
        
        # owner_team is optional, so don't check it in the assertion
    
    def test_register_agent_mapping_conflict(self, mock_cams_client, test_client):
        """Test agent registration with conflicting agent address."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        
        # Test data
        agent_data = {
            "ai_agent_address": TEST_AGENT_ADDRESS,
            "inbox_destination_type": "GCP_PUBSUB_TOPIC",
            "inbox_name": "projects/test/topics/test-agent-inbox"
        }
        
        # Make request
        response = test_client.post("/v1/agent-inboxes", json=agent_data)
        
        # Assertions
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_get_agent_mapping_success(self, mock_cams_client, test_client):
        """Test successful agent mapping retrieval."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        
        # Make request
        response = test_client.get(f"/v1/agent-inboxes/{TEST_AGENT_ADDRESS}")
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["ai_agent_address"] == TEST_AGENT_ADDRESS
        
        # Verify CAMS client was called correctly
        mock_cams_client.get_agent_mapping.assert_awaited_once_with(TEST_AGENT_ADDRESS)
    
    def test_get_agent_mapping_not_found(self, mock_cams_client, test_client):
        """Test agent mapping retrieval for non-existent agent."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=None)
        
        # Make request
        response = test_client.get(f"/v1/agent-inboxes/nonexistent@example.com")
        
        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_agent_mapping_success(self, mock_cams_client, test_client):
        """Test successful agent mapping update."""
        # Setup mocks
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        updated_mapping = {**TEST_AGENT_MAPPING, "status": "INACTIVE", "description": "Updated description"}
        mock_cams_client.update_agent_mapping = AsyncMock(return_value=updated_mapping)
        
        # Test data
        update_data = {
            "status": "INACTIVE",
            "description": "Updated description"
        }
        
        # Make request
        response = test_client.put(f"/v1/agent-inboxes/{TEST_AGENT_ADDRESS}", json=update_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "INACTIVE"
        assert response_data["description"] == "Updated description"
        
        # Verify CAMS client was called correctly
        mock_cams_client.get_agent_mapping.assert_awaited_once_with(TEST_AGENT_ADDRESS)
        mock_cams_client.update_agent_mapping.assert_awaited_once_with(
            ai_agent_address=TEST_AGENT_ADDRESS,
            status="INACTIVE",
            description="Updated description",
            updated_by="agent_management_api/update"
        )
    
    def test_update_agent_mapping_invalid_status(self, mock_cams_client, test_client):
        """Test agent mapping update with invalid status."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        
        # Test data with invalid status
        update_data = {
            "status": "INVALID_STATUS"
        }
        
        # Make request
        response = test_client.put(f"/v1/agent-inboxes/{TEST_AGENT_ADDRESS}", json=update_data)
        
        # Assertions
        assert response.status_code == 422  # Validation error
        assert "Status must be either 'ACTIVE' or 'INACTIVE'" in response.text
    
    def test_delete_agent_mapping_success(self, mock_cams_client, test_client):
        """Test successful agent mapping deletion."""
        # Setup mocks
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        mock_cams_client.delete_agent_mapping = AsyncMock(return_value=True)
        
        # Make request
        response = test_client.delete(f"/v1/agent-inboxes/{TEST_AGENT_ADDRESS}")
        
        # Assertions
        assert response.status_code == 204  # No content
        
        # Verify CAMS client was called correctly
        mock_cams_client.get_agent_mapping.assert_awaited_once_with(TEST_AGENT_ADDRESS)
        mock_cams_client.delete_agent_mapping.assert_awaited_once_with(TEST_AGENT_ADDRESS)
    
    def test_delete_agent_mapping_not_found(self, mock_cams_client, test_client):
        """Test agent mapping deletion for non-existent agent."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=None)
        
        # Make request
        response = test_client.delete(f"/v1/agent-inboxes/nonexistent@example.com")
        
        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_cams_error_handling(self, mock_cams_client, test_client):
        """Test error handling when CAMS client raises an exception."""
        # Setup mock to raise an exception
        mock_cams_client.get_agent_mapping = AsyncMock()
        mock_cams_client.get_agent_mapping.side_effect = Exception("CAMS connection error")
        
        # Test data
        agent_data = {
            "ai_agent_address": TEST_AGENT_ADDRESS,
            "inbox_destination_type": "GCP_PUBSUB_TOPIC",
            "inbox_name": "projects/test/topics/test-agent-inbox"
        }
        
        # Test all endpoints that call get_agent_mapping
        response = test_client.get(f"/v1/agent-inboxes/{TEST_AGENT_ADDRESS}")
        assert response.status_code == 500
        
        response = test_client.put(
            f"/v1/agent-inboxes/{TEST_AGENT_ADDRESS}", 
            json={"status": "INACTIVE"}
        )
        assert response.status_code == 500
        
        response = test_client.delete(f"/v1/agent-inboxes/{TEST_AGENT_ADDRESS}")
        assert response.status_code == 500
