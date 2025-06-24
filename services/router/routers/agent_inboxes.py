"""
Agent Inbox management API endpoints.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Models ---
class AgentInboxCreate(BaseModel):
    """Model for creating a new agent inbox."""
    ai_agent_address: str = Field(..., description="Unique address of the AI agent")
    inbox_destination_type: str = Field(..., description="Type of the inbox destination (e.g., GCP_PUBSUB_TOPIC, HTTP_ENDPOINT)")
    inbox_name: str = Field(..., description="Name or identifier of the inbox")
    description: Optional[str] = Field(None, description="Optional description of the agent inbox")
    owner_team: Optional[str] = Field(None, description="Team responsible for this agent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class AgentInboxResponse(AgentInboxCreate):
    """Response model for agent inbox operations."""
    status: str = Field(..., description="Current status of the agent inbox")
    registration_timestamp: str = Field(..., description="ISO 8601 timestamp of registration")
    last_updated_timestamp: str = Field(..., description="ISO 8601 timestamp of last update")
    updated_by: str = Field(..., description="Identity of who last updated this mapping")

# --- Services ---
class AgentInboxService:
    """Service for managing agent inboxes."""
    
    def __init__(self):
        # In a real implementation, this would be a database client
        self.inboxes = {}
    
    async def create_inbox(self, inbox: AgentInboxCreate, updated_by: str = "system") -> AgentInboxResponse:
        """Create a new agent inbox."""
        if inbox.ai_agent_address in self.inboxes:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Agent with address '{inbox.ai_agent_address}' already exists."
            )
        
        now = datetime.utcnow().isoformat()
        inbox_data = inbox.dict()
        inbox_data.update({
            "status": "ACTIVE",
            "registration_timestamp": now,
            "last_updated_timestamp": now,
            "updated_by": updated_by
        })
        
        self.inboxes[inbox.ai_agent_address] = inbox_data
        return AgentInboxResponse(**inbox_data)
    
    async def get_inbox(self, ai_agent_address: str) -> Optional[AgentInboxResponse]:
        """Retrieve an agent inbox by address."""
        inbox = self.inboxes.get(ai_agent_address)
        if not inbox:
            return None
        return AgentInboxResponse(**inbox)
    
    async def update_inbox(
        self, 
        ai_agent_address: str, 
        updates: Dict[str, Any], 
        updated_by: str = "system"
    ) -> AgentInboxResponse:
        """Update an existing agent inbox."""
        if ai_agent_address not in self.inboxes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with address '{ai_agent_address}' not found."
            )
        
        inbox = self.inboxes[ai_agent_address]
        # Update only the provided fields
        for field, value in updates.items():
            if field in inbox and field not in ["ai_agent_address", "registration_timestamp"]:
                inbox[field] = value
        
        inbox["last_updated_timestamp"] = datetime.utcnow().isoformat()
        inbox["updated_by"] = updated_by
        
        return AgentInboxResponse(**inbox)
    
    async def delete_inbox(self, ai_agent_address: str) -> None:
        """Delete an agent inbox."""
        if ai_agent_address not in self.inboxes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with address '{ai_agent_address}' not found."
            )
        del self.inboxes[ai_agent_address]

# Initialize service
inbox_service = AgentInboxService()

# --- API Endpoints ---
@router.post(
    "",
    response_model=AgentInboxResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent inbox",
    description="Register a new agent inbox with the message router."
)
async def register_agent_inbox(
    inbox: AgentInboxCreate,
    service: AgentInboxService = Depends(lambda: inbox_service)
) -> AgentInboxResponse:
    """Register a new agent inbox."""
    return await service.create_inbox(inbox)

@router.get(
    "/{ai_agent_address}",
    response_model=AgentInboxResponse,
    summary="Get agent inbox details",
    description="Retrieve details for a specific agent inbox by address."
)
async def get_agent_inbox(
    ai_agent_address: str = Path(..., description="Address of the AI agent"),
    service: AgentInboxService = Depends(lambda: inbox_service)
) -> AgentInboxResponse:
    """Get details for a specific agent inbox."""
    inbox = await service.get_inbox(ai_agent_address)
    if not inbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with address '{ai_agent_address}' not found."
        )
    return inbox

@router.put(
    "/{ai_agent_address}",
    response_model=AgentInboxResponse,
    summary="Update agent inbox",
    description="Update details for an existing agent inbox."
)
async def update_agent_inbox(
    ai_agent_address: str = Path(..., description="Address of the AI agent"),
    updates: Dict[str, Any] = {},
    service: AgentInboxService = Depends(lambda: inbox_service)
) -> AgentInboxResponse:
    """Update an existing agent inbox."""
    return await service.update_inbox(ai_agent_address, updates)

@router.delete(
    "/{ai_agent_address}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent inbox",
    description="Delete an agent inbox registration."
)
async def delete_agent_inbox(
    ai_agent_address: str = Path(..., description="Address of the AI agent"),
    service: AgentInboxService = Depends(lambda: inbox_service)
) -> None:
    """Delete an agent inbox."""
    await service.delete_inbox(ai_agent_address)
    return None
