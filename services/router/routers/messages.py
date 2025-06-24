"""
Message router for handling message ingestion and routing.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, validator, HttpUrl
import json
from services.router.cams_client import CAMSClient

# Initialize CAMS client
cams_client = CAMSClient()

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
        self.cams_client = cams_client
    
    async def route_message(self, message: MessageRequest) -> MessageResponse:
        """
        Route a message to the appropriate destination.
        
        Args:
            message: The message to route
            
        Returns:
            MessageResponse: The result of the routing operation
            
        Raises:
            HTTPException: If there's an error routing the message
        """
        try:
            logger.info(f"Routing message {message.message_id} to {message.recipient_address}")
            
            # Get routing information from CAMS
            agent_mapping = await self.cams_client.get_agent_mapping(message.recipient_address)
            
            if not agent_mapping:
                error_msg = f"No mapping found for agent: {message.recipient_address}"
                logger.warning(error_msg)
                return MessageResponse(
                    message_id=message.message_id,
                    status="error",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={"error": error_msg}
                )
            
            # Check if agent is active
            if agent_mapping.get("status") != "ACTIVE":
                error_msg = f"Agent {message.recipient_address} is not active"
                logger.warning(error_msg)
                return MessageResponse(
                    message_id=message.message_id,
                    status="error",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    details={"error": error_msg}
                )
            
            # TODO: Implement actual routing logic based on agent_mapping
            # For now, just log and return success
            logger.info(f"Successfully routed message {message.message_id} to {message.recipient_address}")
            
            # Update last health check timestamp if this is a health check message
            if message.message_type == "HEALTH_CHECK":
                try:
                    await self.cams_client.update_agent_mapping(
                        ai_agent_address=message.recipient_address,
                        updated_by="system/health-check",
                        last_health_check_timestamp=datetime.now(timezone.utc).isoformat()
                    )
                except Exception as e:
                    logger.error(f"Failed to update health check timestamp for {message.recipient_address}: {e}")
            
            return MessageResponse(
                message_id=message.message_id,
                status="routed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={
                    "routing_info": {
                        "inbox_destination_type": agent_mapping.get("inboxDestinationType"),
                        "inbox_name": agent_mapping.get("inboxName"),
                        "status": agent_mapping.get("status")
                    }
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Error routing message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
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
    router: MessageRouter = Depends(lambda: MessageRouter(cams_client=cams_client))
) -> MessageResponse:
    """
    Handle message ingestion and routing.
    
    This endpoint accepts a message and routes it to the appropriate destination
    based on the recipient address and CAMS configuration.
    """
    return await router.route_message(message)
