"""
Async CAMS (Centralized Agent Mapping Service) API client.
"""
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import httpx
import json

logger = logging.getLogger(__name__)

class CAMSConfig(BaseModel):
    """Configuration for the CAMS client."""
    base_url: str = Field("http://cams-service:8080", description="Base URL for the CAMS API")
    timeout: int = Field(30, description="Request timeout in seconds")
    retry_attempts: int = Field(3, description="Number of retry attempts for failed requests")
    api_key: Optional[str] = Field(None, description="API key for authentication")

class CAMSClient:
    """Async client for interacting with the CAMS API."""
    
    def __init__(self, config: Optional[CAMSConfig] = None):
        self.config = config or CAMSConfig()
        self.client = None
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.config.api_key:
            self._headers["Authorization"] = f"Bearer {self.config.api_key}"
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def connect(self):
        """Initialize the HTTP client."""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._headers
            )
    
    async def close(self):
        """Close the HTTP client."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
    
    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        if self.client is None or self.client.is_closed:
            await self.connect()
        
        last_error = None
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self.client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else {}
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    # Don't retry 4xx errors
                    raise
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed with status {e.response.status_code}")
            except (httpx.RequestError, json.JSONDecodeError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < self.config.retry_attempts - 1:
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise last_error or Exception("Unknown error in _request")
    
    # --- Agent Mapping Operations ---
    
    async def register_agent_mapping(
        self,
        ai_agent_address: str,
        inbox_destination_type: str,
        inbox_name: str,
        description: Optional[str] = None,
        owner_team: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a new agent mapping."""
        data = {
            "aiAgentAddress": ai_agent_address,
            "inboxDestinationType": inbox_destination_type,
            "inboxName": inbox_name,
        }
        if description is not None:
            data["description"] = description
        if owner_team is not None:
            data["ownerTeam"] = owner_team
        if metadata is not None:
            data["metadata"] = metadata
            
        return await self._request("POST", "/v1/agent-mappings", json=data)
    
    async def get_agent_mapping(self, ai_agent_address: str) -> Optional[Dict[str, Any]]:
        """Retrieve an agent mapping by address."""
        try:
            return await self._request("GET", f"/v1/agent-mappings/{ai_agent_address}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def update_agent_mapping(
        self,
        ai_agent_address: str,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing agent mapping."""
        data = updates.copy()
        if updated_by is not None:
            data["updatedBy"] = updated_by
        return await self._request("PUT", f"/v1/agent-mappings/{ai_agent_address}", json=data)
    
    async def delete_agent_mapping(self, ai_agent_address: str) -> None:
        """Delete an agent mapping."""
        try:
            await self._request("DELETE", f"/v1/agent-mappings/{ai_agent_address}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:  # Ignore 404 on delete
                raise
    
    async def list_agent_mappings(
        self,
        status: Optional[str] = None,
        owner_team: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """List agent mappings with optional filtering and pagination."""
        params = {"page": page, "pageSize": page_size}
        if status is not None:
            params["status"] = status
        if owner_team is not None:
            params["ownerTeam"] = owner_team
            
        return await self._request("GET", "/v1/agent-mappings", params=params)
    
    # --- Health Check ---
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the CAMS service."""
        try:
            return await self._request("GET", "/health")
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# Default client instance for convenience
_default_client = None

async def get_default_client() -> CAMSClient:
    """Get or create a default CAMS client instance."""
    global _default_client
    if _default_client is None:
        _default_client = CAMSClient()
        await _default_client.connect()
    return _default_client
