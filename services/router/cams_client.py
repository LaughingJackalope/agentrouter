"""
CAMS Client for the Router Service.

This module provides a client for interacting with the Central Agent Mapping Service (CAMS).
It uses the cams_repository for persistent storage.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from services.cams.cams_repository import (
    register_agent_mapping,
    get_agent_mapping,
    update_agent_mapping_details,
    delete_agent_mapping,
    list_agent_mappings,
    CAMSRepositoryError,
    DuplicateAgentError,
    AgentNotFoundError
)

logger = logging.getLogger(__name__)

class CAMSClient:
    """Client for interacting with the Central Agent Mapping Service."""
    
    @staticmethod
    async def register_agent_mapping(
        ai_agent_address: str,
        inbox_destination_type: str,
        inbox_name: str,
        description: str = None,
        owner_team: str = None,
        updated_by: str = "router_service"
    ) -> Dict[str, Any]:
        """Register a new agent mapping."""
        try:
            result = await register_agent_mapping(
                ai_agent_address=ai_agent_address,
                inbox_destination_type=inbox_destination_type,
                inbox_name=inbox_name,
                description=description,
                owner_team=owner_team,
                updated_by=updated_by
            )
            return {
                "aiAgentAddress": result["ai_agent_address"],
                "inboxDestinationType": result["inbox_destination_type"],
                "inboxName": result["inbox_name"],
                "status": result["status"],
                "registrationTimestamp": result["registration_timestamp"].isoformat(),
                "lastUpdatedTimestamp": result["last_updated_timestamp"].isoformat(),
                "description": result["description"],
                "ownerTeam": result["owner_team"],
                "updatedBy": result["updated_by"]
            }
        except DuplicateAgentError as e:
            raise ValueError(f"Agent with address '{ai_agent_address}' already exists.") from e
        except CAMSRepositoryError as e:
            logger.error(f"Failed to register agent {ai_agent_address}: {e}")
            raise
    
    @staticmethod
    async def get_agent_mapping(ai_agent_address: str) -> Optional[Dict[str, Any]]:
        """Retrieve an agent mapping by address."""
        try:
            result = await get_agent_mapping(ai_agent_address)
            if not result:
                return None
                
            return {
                "aiAgentAddress": result["ai_agent_address"],
                "inboxDestinationType": result["inbox_destination_type"],
                "inboxName": result["inbox_name"],
                "status": result["status"],
                "registrationTimestamp": result["registration_timestamp"].isoformat(),
                "lastUpdatedTimestamp": result["last_updated_timestamp"].isoformat(),
                "description": result["description"],
                "ownerTeam": result["owner_team"],
                "updatedBy": result["updated_by"]
            }
        except CAMSRepositoryError as e:
            logger.error(f"Failed to fetch agent {ai_agent_address}: {e}")
            raise
    
    @staticmethod
    async def update_agent_status(
        ai_agent_address: str,
        new_status: str,
        updated_by: str = "router_service"
    ) -> bool:
        """Update an agent's status."""
        try:
            result = await update_agent_mapping_details(
                ai_agent_address=ai_agent_address,
                updated_by=updated_by,
                status=new_status
            )
            return bool(result)
        except AgentNotFoundError as e:
            logger.warning(f"Agent not found: {ai_agent_address}")
            return False
        except CAMSRepositoryError as e:
            logger.error(f"Failed to update status for agent {ai_agent_address}: {e}")
            raise
    
    @staticmethod
    async def update_agent_mapping_details(
        ai_agent_address: str,
        updated_by: str = "router_service",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update one or more fields of an agent mapping."""
        try:
            result = await update_agent_mapping_details(
                ai_agent_address=ai_agent_address,
                updated_by=updated_by,
                **kwargs
            )
            
            if not result:
                return None
                
            return {
                "aiAgentAddress": result["ai_agent_address"],
                "inboxDestinationType": result["inbox_destination_type"],
                "inboxName": result["inbox_name"],
                "status": result["status"],
                "registrationTimestamp": result["registration_timestamp"].isoformat(),
                "lastUpdatedTimestamp": result["last_updated_timestamp"].isoformat(),
                "description": result["description"],
                "ownerTeam": result["owner_team"],
                "updatedBy": result["updated_by"]
            }
        except AgentNotFoundError as e:
            logger.warning(f"Agent not found: {ai_agent_address}")
            return None
        except CAMSRepositoryError as e:
            logger.error(f"Failed to update agent {ai_agent_address}: {e}")
            raise
    
    @staticmethod
    async def delete_agent_mapping(ai_agent_address: str) -> bool:
        """Delete an agent mapping."""
        try:
            await delete_agent_mapping(ai_agent_address)
            return True
        except AgentNotFoundError:
            logger.warning(f"Agent not found: {ai_agent_address}")
            return False
        except CAMSRepositoryError as e:
            logger.error(f"Failed to delete agent {ai_agent_address}: {e}")
            raise
    
    @staticmethod
    async def list_agent_mappings(
        status: str = None,
        owner_team: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List agent mappings with optional filtering."""
        try:
            results = await list_agent_mappings(
                status=status,
                owner_team=owner_team,
                limit=limit,
                offset=offset
            )
            
            return {
                "items": [{
                    "aiAgentAddress": item["ai_agent_address"],
                    "inboxDestinationType": item["inbox_destination_type"],
                    "inboxName": item["inbox_name"],
                    "status": item["status"],
                    "registrationTimestamp": item["registration_timestamp"].isoformat(),
                    "lastUpdatedTimestamp": item["last_updated_timestamp"].isoformat(),
                    "description": item["description"],
                    "ownerTeam": item["owner_team"],
                    "updatedBy": item["updated_by"]
                } for item in results],
                "total": len(results),
                "limit": limit,
                "offset": offset
            }
        except CAMSRepositoryError as e:
            logger.error(f"Failed to list agent mappings: {e}")
            raise
