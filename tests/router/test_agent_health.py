"""
Tests for the Agent Health Check API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta
import json

from services.router.main import app
from services.router.message_router_service import cams_client

client = TestClient(app)

# Test data
TEST_AGENT_ADDRESS = "test-agent@example.com"
TEST_AGENT_MAPPING = {
    "ai_agent_address": TEST_AGENT_ADDRESS,
    "inbox_destination_type": "GCP_PUBSUB_TOPIC",
    "inbox_name": "projects/test/topics/test-agent-inbox",
    "status": "ACTIVE",
    "registration_timestamp": "2025-01-01T00:00:00Z",
    "last_updated_timestamp": "2025-01-01T00:00:00Z",
}

# Fixtures
@pytest.fixture
def mock_cams_client():
    with patch('services.router.message_router_service.cams_client') as mock:
        yield mock

# Test cases
class TestAgentHealthCheckAPI:
    def test_report_health_status_success(self, mock_cams_client):
        """Test successful health status reporting."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        mock_cams_client.update_agent_mapping = AsyncMock()
        
        # Test data
        health_data = {
            "ai_agent_address": TEST_AGENT_ADDRESS,
            "status": "HEALTHY",
            "details": {"component": "test", "metrics": {}},
            "timestamp": "2025-01-01T12:00:00Z"
        }
        
        # Make request
        response = client.post("/v1/agent-health-check", json=health_data)
        
        # Assertions
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert "Health status recorded" in response_data["message"]
        
        # Verify CAMS client was called correctly
        mock_cams_client.get_agent_mapping.assert_awaited_once_with(TEST_AGENT_ADDRESS)
        mock_cams_client.update_agent_mapping.assert_awaited_once()
        
        # Check that the update included the health check timestamp
        call_args = mock_cams_client.update_agent_mapping.await_args[1]
        assert call_args["ai_agent_address"] == TEST_AGENT_ADDRESS
        assert "last_health_check_timestamp" in call_args
        assert call_args["updated_by"] == "agent_health_check"
    
    def test_report_health_status_unhealthy(self, mock_cams_client):
        """Test reporting UNHEALTHY status marks agent as INACTIVE."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=TEST_AGENT_MAPPING)
        mock_cams_client.update_agent_mapping = AsyncMock()
        
        # Test data
        health_data = {
            "ai_agent_address": TEST_AGENT_ADDRESS,
            "status": "UNHEALTHY"
        }
        
        # Make request
        response = client.post("/v1/agent-health-check", json=health_data)
        
        # Assertions
        assert response.status_code == 200
        
        # Verify agent was marked as INACTIVE
        call_args = mock_cams_client.update_agent_mapping.await_args[1]
        assert call_args["status"] == "INACTIVE"
    
    def test_agent_not_found(self, mock_cams_client):
        """Test health check for non-existent agent returns 404."""
        # Setup mock
        mock_cams_client.get_agent_mapping = AsyncMock(return_value=None)
        
        # Test data
        health_data = {
            "ai_agent_address": "nonexistent@example.com",
            "status": "HEALTHY"
        }
        
        # Make request
        response = client.post("/v1/agent-health-check", json=health_data)
        
        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_invalid_status(self, mock_cams_client):
        """Test validation of status field."""
        # Test data
        health_data = {
            "ai_agent_address": TEST_AGENT_ADDRESS,
            "status": "INVALID_STATUS"
        }
        
        # Make request
        response = client.post("/v1/agent-health-check", json=health_data)
        
        # Assertions
        assert response.status_code == 400
        assert "must be 'HEALTHY' or 'UNHEALTHY'" in response.json()["detail"]
    
    def test_missing_required_fields(self, mock_cams_client):
        """Test validation of required fields."""
        # Missing status
        response = client.post(
            "/v1/agent-health-check",
            json={"ai_agent_address": TEST_AGENT_ADDRESS}
        )
        assert response.status_code == 422  # Validation error
        
        # Missing ai_agent_address
        response = client.post(
            "/v1/agent-health-check",
            json={"status": "HEALTHY"}
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_cams_error_handling(self, mock_cams_client):
        """Test error handling when CAMS client raises an exception."""
        # Setup mock to raise an exception
        mock_cams_client.get_agent_mapping = AsyncMock()
        mock_cams_client.get_agent_mapping.side_effect = Exception("CAMS connection error")
        
        # Test data
        health_data = {
            "ai_agent_address": TEST_AGENT_ADDRESS,
            "status": "HEALTHY"
        }
        
        # Make request
        response = client.post("/v1/agent-health-check", json=health_data)
        
        # Assertions
        assert response.status_code == 500
        assert "internal server error" in response.json()["detail"].lower()
