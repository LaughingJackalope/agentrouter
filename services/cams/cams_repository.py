"""
Central Agent Mapping Service (CAMS) Repository

This module provides an asynchronous implementation of the CAMS API using PostgreSQL with asyncpg.
"""
import os
import logging
import asyncpg
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

# Configure logging
logger = logging.getLogger('cams')

# Database connection pool
_pool = None

class CAMSRepositoryError(Exception):
    """Base exception for CAMS repository errors."""
    pass

class DuplicateAgentError(CAMSRepositoryError):
    """Raised when trying to register an agent that already exists."""
    pass

class AgentNotFoundError(CAMSRepositoryError):
    """Raised when an agent is not found in the database."""
    pass

async def get_connection_pool():
    """Get or create a connection pool."""
    global _pool
    if _pool is None:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'cams'),
            'min_size': 1,
            'max_size': 10
        }
        _pool = await asyncpg.create_pool(**db_config)
    return _pool

async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

async def _execute(query: str, *args) -> str:
    """Execute a write query and return the status."""
    pool = await get_connection_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.execute(query, *args)
            return result
        except asyncpg.UniqueViolationError as e:
            raise DuplicateAgentError(f"Agent already exists: {e}")
        except asyncpg.PostgresError as e:
            raise CAMSRepositoryError(f"Database error: {e}")

async def _fetchrow(query: str, *args) -> Optional[Dict[str, Any]]:
    """Execute a query and return a single row."""
    pool = await get_connection_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
        except asyncpg.PostgresError as e:
            raise CAMSRepositoryError(f"Database error: {e}")

async def _fetch(query: str, *args) -> List[Dict[str, Any]]:
    """Execute a query and return multiple rows."""
    pool = await get_connection_pool()
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
        except asyncpool.PostgresError as e:
            raise CAMSRepositoryError(f"Database error: {e}")

async def register_agent_mapping(
    ai_agent_address: str,
    inbox_destination_type: str,
    inbox_name: str,
    description: str = None,
    owner_team: str = None,
    updated_by: str = None,
    status: str = 'ACTIVE'
) -> Dict[str, Any]:
    """Register a new agent mapping."""
    query = """
        INSERT INTO agent_inboxes (
            ai_agent_address, inbox_destination_type, inbox_name,
            status, description, owner_team, updated_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    try:
        result = await _fetchrow(
            query,
            ai_agent_address,
            inbox_destination_type.upper(),
            inbox_name,
            status.upper(),
            description,
            owner_team,
            updated_by
        )
        return result
    except DuplicateAgentError:
        raise
    except CAMSRepositoryError as e:
        logger.error(f"Failed to register agent {ai_agent_address}: {e}")
        raise

async def get_agent_mapping(ai_agent_address: str) -> Optional[Dict[str, Any]]:
    """Retrieve an agent mapping by address."""
    query = "SELECT * FROM agent_inboxes WHERE ai_agent_address = $1"
    try:
        return await _fetchrow(query, ai_agent_address)
    except CAMSRepositoryError as e:
        logger.error(f"Failed to fetch agent {ai_agent_address}: {e}")
        raise

async def update_agent_status(
    ai_agent_address: str,
    new_status: str,
    updated_by: str = None
) -> bool:
    """Update an agent's status."""
    query = """
        UPDATE agent_inboxes 
        SET status = $1, updated_by = $2
        WHERE ai_agent_address = $3
        RETURNING *
    """

    try:
        result = await _fetchrow(
            query,
            new_status.upper(),
            updated_by,
            ai_agent_address
        )
        if not result:
            raise AgentNotFoundError(f"Agent {ai_agent_address} not found")
        return True
    except CAMSRepositoryError as e:
        logger.error(f"Failed to update status for agent {ai_agent_address}: {e}")
        raise

async def update_agent_mapping_details(
    ai_agent_address: str,
    updated_by: str = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """Update one or more fields of an agent mapping."""
    if not kwargs:
        raise ValueError("No fields to update")

    allowed_fields = {
        'inbox_destination_type',
        'inbox_name',
        'status',
        'description',
        'owner_team',
        'last_health_check_timestamp'
    }

    # Validate fields to update
    invalid_fields = set(kwargs.keys()) - allowed_fields
    if invalid_fields:
        raise ValueError(f"Invalid fields to update: {', '.join(invalid_fields)}")

    # Special handling for status to ensure uppercase
    if 'status' in kwargs:
        kwargs['status'] = kwargs['status'].upper()

    # Special handling for health check timestamp
    if 'last_health_check_timestamp' in kwargs and kwargs['last_health_check_timestamp'] is None:
        kwargs['last_health_check_timestamp'] = datetime.now(timezone.utc)

    # Build the SET clause
    set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])

    query = f"""
        UPDATE agent_inboxes
        SET {set_clause}, updated_by = $1
        WHERE ai_agent_address = ${len(kwargs) + 2}
        RETURNING *
    """

    try:
        result = await _fetchrow(
            query,
            updated_by,
            *kwargs.values(),
            ai_agent_address
        )
        if not result:
            raise AgentNotFoundError(f"Agent {ai_agent_address} not found")
        return result
    except CAMSRepositoryError as e:
        logger.error(f"Failed to update agent {ai_agent_address}: {e}")
        raise

async def delete_agent_mapping(ai_agent_address: str) -> bool:
    """Delete an agent mapping."""
    query = """
        DELETE FROM agent_inboxes 
        WHERE ai_agent_address = $1
        RETURNING ai_agent_address
    """
    try:
        result = await _fetchrow(query, ai_agent_address)
        if not result:
            raise AgentNotFoundError(f"Agent {ai_agent_address} not found")
        return True
    except CAMSRepositoryError as e:
        logger.error(f"Failed to delete agent {ai_agent_address}: {e}")
        raise

async def list_agent_mappings(
    status: str = None,
    owner_team: str = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List agent mappings with optional filtering."""
    conditions = []
    params = []
    param_count = 0

    if status is not None:
        param_count += 1
        conditions.append(f"status = ${param_count}")
        params.append(status.upper())

    if owner_team is not None:
        param_count += 1
        conditions.append(f"owner_team = ${param_count}")
        params.append(owner_team)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT * FROM agent_inboxes
        {where_clause}
        ORDER BY registration_timestamp DESC
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
    """

    params.extend([limit, offset])

    try:
        return await _fetch(query, *params)
    except CAMSRepositoryError as e:
        logger.error(f"Failed to list agent mappings: {e}")
        raise
