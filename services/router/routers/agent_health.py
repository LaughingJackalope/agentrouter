"""
Agent Health Check API endpoints.

This module provides endpoints for agents to report their health status.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from services.router.message_router_service import cams_client, metrics, log_context, timed_operation

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Models ---
class HealthCheckRequest(BaseModel):
    """Request model for agent health check."""
    ai_agent_address: str = Field(..., description="Address of the AI agent")
    status: str = Field(..., description="Health status (HEALTHY/UNHEALTHY)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")
    timestamp: Optional[datetime] = Field(None, description="When the health check was performed")

class HealthCheckResponse(BaseModel):
    """Response model for health check operations."""
    status: str = Field(..., description="Status of the health check operation")
    message: str = Field(..., description="Detailed message about the operation result")
    timestamp: str = Field(..., description="When the response was generated")

# --- API Endpoints ---
@router.post(
    "/agent-health-check",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Report agent health status",
    description="Report the health status of an AI agent to the Central Agent Mapping Service (CAMS)."
)
@timed_operation("agent_health_check")
async def report_agent_health(
    health_data: HealthCheckRequest
) -> HealthCheckResponse:
    """
    Report the health status of an AI agent.
    
    This endpoint allows AI agents to report their health status to the system.
    The status is recorded in the Central Agent Mapping Service (CAMS).
    """
    ai_agent_address = health_data.ai_agent_address
    health_status = health_data.status.upper()
    
    with log_context(ai_agent_address=ai_agent_address, health_status=health_status):
        try:
            # Validate health status
            if health_status not in ["HEALTHY", "UNHEALTHY"]:
                error_msg = "Invalid health status. Must be 'HEALTHY' or 'UNHEALTHY'."
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            # Get the current agent mapping to check if it exists
            agent_mapping = await cams_client.get_agent_mapping(ai_agent_address)
            if not agent_mapping:
                error_msg = f"Agent {ai_agent_address} not found in CAMS"
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg
                )
            
            # Prepare update data
            update_data = {
                "last_health_check_timestamp": health_data.timestamp or datetime.now(timezone.utc),
                "updated_by": "agent_health_check"
            }
            
            # If status is UNHEALTHY, mark the agent as INACTIVE
            if health_status == "UNHEALTHY":
                update_data["status"] = "INACTIVE"
                logger.warning(f"Agent {ai_agent_address} reported as UNHEALTHY, marking as INACTIVE")
            
            # Update the agent mapping with health check info
            await cams_client.update_agent_mapping(
                ai_agent_address=ai_agent_address,
                **update_data
            )
            
            # Log and return success
            logger.info(f"Recorded {health_status} health status for agent {ai_agent_address}")
            
            # Record metrics
            metrics.increment_counter("agent_health_reported", {
                "status": "success",
                "health_status": health_status.lower()
            })
            
            return HealthCheckResponse(
                status="success",
                message=f"Health status recorded for agent {ai_agent_address}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
        except HTTPException:
            metrics.increment_counter("agent_health_reported", {"status": "error", "error_type": "client_error"})
            raise
            
        except Exception as e:
            error_msg = f"Failed to record health status: {str(e)}"
            logger.error(error_msg, exc_info=True)
            metrics.increment_counter("agent_health_reported", {"status": "error", "error_type": "server_error"})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the health check"
            )
