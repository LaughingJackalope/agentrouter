"""
Message router for handling message ingestion and routing.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json
from ...services.cams.cams_api_pseudo import getAgentMapping

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Models ---
class MessageRequest(BaseModel):
    """Request model for message ingestion."""
    message_id: str = Field(..., description="Unique identifier for the message")
    sender_address: str = Field(..., description="Address of the message sender")
    recipient_address: str = Field(..., description="Address of the message recipient")
    message_type: str = Field(..., description="Type of the message")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), 
                          description="ISO 8601 timestamp of message creation")
    metadata: Dict[str, Any] = Field(default_factory=dict, 
                                    description="Additional metadata about the message")

    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except (ValueError, TypeError):
            raise ValueError("Invalid timestamp format. Expected ISO 8601 format.")

class MessageResponse(BaseModel):
    """Response model for message ingestion."""
    message_id: str
    status: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

# --- Services ---
class MessageRouter:
    """Core message routing logic."""
    
    def __init__(self, cams_client=None):
        self.cams_client = cams_client or CAMSClient()
    
    async def route_message(self, message: MessageRequest) -> MessageResponse:
        """Route a message to the appropriate destination."""
        try:
            # Get routing information from CAMS
            agent_mapping = await self.cams_client.get_agent_mapping(message.recipient_address)
            
            if not agent_mapping:
                logger.warning(f"No mapping found for agent: {message.recipient_address}")
                return MessageResponse(
                    message_id=message.message_id,
                    status="error",
                    timestamp=datetime.utcnow().isoformat(),
                    details={"error": f"No mapping found for agent: {message.recipient_address}"}
                )
            
            # TODO: Implement actual routing logic based on agent_mapping
            # For now, just log and return success
            logger.info(f"Routing message {message.message_id} to {message.recipient_address}")
            
            return MessageResponse(
                message_id=message.message_id,
                status="routed",
                timestamp=datetime.utcnow().isoformat(),
                details={"routing_info": agent_mapping}
            )
            
        except Exception as e:
            logger.error(f"Error routing message: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error routing message: {str(e)}"
            )

# --- API Endpoints ---
@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Route a message",
    description="Ingest and route a message to the appropriate destination."
)
async def route_message(
    message: MessageRequest,
    router: MessageRouter = Depends(lambda: MessageRouter())
) -> MessageResponse:
    """
    Handle message ingestion and routing.
    
    This endpoint accepts a message and routes it to the appropriate destination
    based on the recipient address and CAMS configuration.
    """
    return await router.route_message(message)
