"""
Agent Management API for the Router Service.

This module provides FastAPI endpoints for managing agent mappings in the Central Agent Mapping Service (CAMS).
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from pydantic import BaseModel, Field, validator
from typing import Optional

from services.router.cams_client import CAMSClient
from services.router.message_router_service import metrics, log_context, timed_operation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/agent-inboxes", tags=["agent-management"])

# Dependency to get CAMS client
def get_cams_client() -> CAMSClient:
    return CAMSClient()

# --- Request/Response Models ---
class AgentMappingBase(BaseModel):
    """Base model for agent mapping data."""
    ai_agent_address: str = Field(..., description="Unique identifier for the AI agent")
    inbox_destination_type: str = Field(..., description="Type of the inbox destination (e.g., 'GCP_PUBSUB_TOPIC')")
    inbox_name: str = Field(..., description="Name/identifier of the inbox")
    description: Optional[str] = Field(None, description="Optional description of the agent mapping")
    owner_team: Optional[str] = Field(None, alias="ownerTeam", description="Team responsible for this agent")
    status: str = Field("ACTIVE", description="Current status of the agent (ACTIVE/INACTIVE)")

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "ai_agent_address": "agent@example.com",
                "inbox_destination_type": "GCP_PUBSUB_TOPIC",
                "inbox_name": "projects/my-project/topics/agent-inbox",
                "description": "Customer support agent",
                "owner_team": "support-team",
                "status": "ACTIVE"
            }
        }

class AgentMappingCreate(AgentMappingBase):
    """Model for creating a new agent mapping."""
    pass

class AgentMappingUpdate(BaseModel):
    """Model for updating an existing agent mapping."""
    inbox_destination_type: Optional[str] = Field(None, description="Type of the inbox destination")
    inbox_name: Optional[str] = Field(None, description="Name/identifier of the inbox")
    description: Optional[str] = Field(None, description="Optional description of the agent mapping")
    owner_team: Optional[str] = Field(None, alias="ownerTeam", description="Team responsible for this agent")
    status: Optional[str] = Field(None, description="Current status of the agent (ACTIVE/INACTIVE)")

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v.upper() not in ["ACTIVE", "INACTIVE"]:
            raise ValueError("Status must be either 'ACTIVE' or 'INACTIVE'")
        return v.upper() if v else v

    class Config:
        allow_population_by_field_name = True

class AgentMappingResponse(AgentMappingBase):
    """Response model for agent mapping operations."""
    registration_timestamp: datetime = Field(..., description="When the agent mapping was registered")
    last_updated_timestamp: datetime = Field(..., description="When the agent mapping was last updated")
    last_health_check_timestamp: Optional[datetime] = Field(None, description="When the agent last reported health")
    updated_by: str = Field(..., description="Who last updated this mapping")

# --- API Endpoints ---
@router.post(
    "",
    response_model=AgentMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent mapping",
    description="Register a new AI agent and its associated inbox details in CAMS."
)
@timed_operation("register_agent_mapping")
async def register_agent_mapping(
    mapping: AgentMappingCreate,
    cams_client: CAMSClient = Depends(get_cams_client)
) -> AgentMappingResponse:
    """
    Register a new agent mapping in the Central Agent Mapping Service (CAMS).
    
    This endpoint creates a new mapping between an AI agent address and its associated
    inbox details, which is used for message routing within the system.
    """
    with log_context(ai_agent_address=mapping.ai_agent_address):
        try:
            # Check if agent already exists
            existing_mapping = await cams_client.get_agent_mapping(mapping.ai_agent_address)
            if existing_mapping:
                error_msg = f"Agent with address '{mapping.ai_agent_address}' already exists"
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=error_msg
                )
            
            # Register the new agent mapping
            new_mapping = await cams_client.register_agent_mapping(
                ai_agent_address=mapping.ai_agent_address,
                inbox_destination_type=mapping.inbox_destination_type,
                inbox_name=mapping.inbox_name,
                description=mapping.description,
                owner_team=mapping.owner_team,
                status=mapping.status,
                updated_by="agent_management_api"
            )
            
            # Record success metric
            metrics.increment_counter("agent_mapping_created", {
                "status": "success",
                "inbox_type": mapping.inbox_destination_type
            })
            
            return AgentMappingResponse(**new_mapping)
            
        except HTTPException:
            metrics.increment_counter("agent_mapping_created", {"status": "error", "error_type": "client_error"})
            raise
        except Exception as e:
            error_msg = f"Failed to register agent mapping: {str(e)}"
            logger.error(error_msg, exc_info=True)
            metrics.increment_counter("agent_mapping_created", {"status": "error", "error_type": "server_error"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while registering the agent mapping"
            )

@router.get(
    "/{ai_agent_address}",
    response_model=AgentMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an agent mapping",
    description="Retrieve the details of a specific agent mapping by AI agent address."
)
@timed_operation("get_agent_mapping")
async def retrieve_agent_mapping(
    ai_agent_address: str = Path(..., description="The AI agent address to look up"),
    cams_client: CAMSClient = Depends(get_cams_client)
) -> AgentMappingResponse:
    """
    Retrieve the details of a specific agent mapping.
    
    This endpoint fetches the current mapping details for the specified AI agent
    address from the Central Agent Mapping Service (CAMS).
    """
    with log_context(ai_agent_address=ai_agent_address):
        try:
            mapping = await cams_client.get_agent_mapping(ai_agent_address)
            if not mapping:
                error_msg = f"Agent mapping not found for {ai_agent_address}"
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            
            metrics.increment_counter("agent_mapping_retrieved", {"status": "success"})
            return AgentMappingResponse(**mapping)
            
        except HTTPException:
            metrics.increment_counter("agent_mapping_retrieved", {"status": "error", "error_type": "not_found"})
            raise
        except Exception as e:
            error_msg = f"Failed to retrieve agent mapping: {str(e)}"
            logger.error(error_msg, exc_info=True)
            metrics.increment_counter("agent_mapping_retrieved", {"status": "error", "error_type": "server_error"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving the agent mapping"
            )

@router.put(
    "/{ai_agent_address}",
    response_model=AgentMappingResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an agent mapping",
    description="Update the details of an existing agent mapping."
)
@timed_operation("update_agent_mapping")
async def update_agent_mapping(
    ai_agent_address: str = Path(..., description="The AI agent address to update"),
    update_data: AgentMappingUpdate = Body(..., description="The fields to update"),
    cams_client: CAMSClient = Depends(get_cams_client)
) -> AgentMappingResponse:
    """
    Update an existing agent mapping in CAMS.
    
    This endpoint allows updating one or more fields of an agent mapping.
    Only the fields provided in the request will be updated.
    """
    with log_context(ai_agent_address=ai_agent_address):
        try:
            # Check if agent exists
            existing_mapping = await cams_client.get_agent_mapping(ai_agent_address)
            if not existing_mapping:
                error_msg = f"Agent mapping not found for {ai_agent_address}"
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            
            # Prepare update data
            update_fields = update_data.dict(exclude_unset=True)
            if not update_fields:
                logger.warning("No valid fields provided for update")
                return AgentMappingResponse(**existing_mapping)
            
            # Convert alias back to snake_case for the CAMS client
            if "ownerTeam" in update_fields:
                update_fields["owner_team"] = update_fields.pop("ownerTeam")
            
            # Add updated_by field
            update_fields["updated_by"] = "agent_management_api/update"
            
            # Update the agent mapping
            updated_mapping = await cams_client.update_agent_mapping(
                ai_agent_address=ai_agent_address,
                **update_fields
            )
            
            if not updated_mapping:
                error_msg = f"Failed to update agent mapping for {ai_agent_address}"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
            
            metrics.increment_counter("agent_mapping_updated", {"status": "success"})
            return AgentMappingResponse(**updated_mapping)
            
        except HTTPException:
            metrics.increment_counter("agent_mapping_updated", {"status": "error", "error_type": "client_error"})
            raise
        except Exception as e:
            error_msg = f"Failed to update agent mapping: {str(e)}"
            logger.error(error_msg, exc_info=True)
            metrics.increment_counter("agent_mapping_updated", {"status": "error", "error_type": "server_error"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the agent mapping"
            )

@router.delete(
    "/{ai_agent_address}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an agent mapping",
    description="Delete an agent mapping from CAMS."
)
@timed_operation("delete_agent_mapping")
async def delete_agent_mapping(
    ai_agent_address: str = Path(..., description="The AI agent address to delete"),
    cams_client: CAMSClient = Depends(get_cams_client)
):
    """
    Delete an agent mapping from CAMS.
    
    This endpoint removes the mapping for the specified AI agent address.
    """
    with log_context(ai_agent_address=ai_agent_address):
        try:
            # Check if agent exists
            existing_mapping = await cams_client.get_agent_mapping(ai_agent_address)
            if not existing_mapping:
                error_msg = f"Agent mapping not found for {ai_agent_address}"
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            
            # Delete the agent mapping
            success = await cams_client.delete_agent_mapping(ai_agent_address)
            
            if not success:
                error_msg = f"Failed to delete agent mapping for {ai_agent_address}"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
            
            metrics.increment_counter("agent_mapping_deleted", {"status": "success"})
            return None
            
        except HTTPException:
            metrics.increment_counter("agent_mapping_deleted", {"status": "error", "error_type": "client_error"})
            raise
        except Exception as e:
            error_msg = f"Failed to delete agent mapping: {str(e)}"
            logger.error(error_msg, exc_info=True)
            metrics.increment_counter("agent_mapping_deleted", {"status": "error", "error_type": "server_error"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the agent mapping"
            )
