# services/cams/cams_api_pseudo.py
# Pseudo-code for Central Agent Mapping Service (CAMS) Core API Operations

import datetime
import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from functools import wraps

# Reuse the MetricsCollector from message_router_service
from services.router.message_router_service import MetricsCollector

# Initialize metrics
metrics = MetricsCollector()

# Configure logging
logger = logging.getLogger('cams')
logger.setLevel(logging.INFO)

# Context manager for database operations
def db_operation(operation: str):
    """Decorator to time database operations and log metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            # Extract aiAgentAddress from args if available
            ai_agent_address = None
            if args and len(args) > 1 and isinstance(args[1], str):
                ai_agent_address = args[1]
            
            log_context = {
                'operation': operation,
                'ai_agent_address': ai_agent_address or 'unknown'
            }
            
            logger.info(f"Starting {operation}", extra=log_context)
            
            try:
                result = func(*args, **kwargs)
                log_context['success'] = True
                return result
            except Exception as e:
                status = 'error'
                log_context.update({
                    'success': False,
                    'error': str(e),
                    'error_type': e.__class__.__name__
                })
                logger.error(f"{operation} failed", exc_info=True, extra=log_context)
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_latency(
                    f"cams_db_operation_duration_seconds",
                    duration,
                    {'operation': operation, 'status': status}
                )
                metrics.increment_counter(
                    f"cams_db_operations_total",
                    {'operation': operation, 'status': status}
                )
                logger.info(
                    f"{operation} completed",
                    extra={
                        **log_context,
                        'duration_seconds': duration,
                        'status': status
                    }
                )
        return wrapper
    return decorator

# Conceptual Database Client
# This is a placeholder for whatever database interaction library/ORM will be used.
# It's assumed that this client handles connection management and sanitizes inputs
# to prevent SQL injection if raw SQL is being constructed.

class DBClient:
    @db_operation("execute_query")
    def execute_query(self, query, params=None):
        """
        Executes a query that modifies data (INSERT, UPDATE, DELETE)
        or a query that might return multiple rows (though not used for that here).
        Returns True for success/row affected, False otherwise, or raises an exception.
        """
        logger.debug("Executing database query", extra={
            'query': query,
            'params': str(params)[:500]  # Truncate long parameters
        })
        
        try:
            # In a real implementation, this would interact with the database.
            # For pseudo-code, we'll assume success if params seem valid for the operation.
            if "INSERT" in query and params and len(params) >= 3:  # Basic check for register
                metrics.increment_counter("cams_db_insert_total", {"table": "agent_mappings"})
                return True
            if "UPDATE" in query and params and len(params) >= 2:  # Basic check for update
                metrics.increment_counter("cams_db_update_total", {"table": "agent_mappings"})
                return True
            if "DELETE" in query and params and len(params) >= 1:  # Basic check for delete
                metrics.increment_counter("cams_db_delete_total", {"table": "agent_mappings"})
                return True
                
            logger.warning("Query validation failed", extra={
                'query': query,
                'params_count': len(params) if params else 0
            })
            return False
            
        except Exception as e:
            logger.error("Database query failed", extra={
                'query': query,
                'error': str(e),
                'error_type': e.__class__.__name__
            })
            metrics.increment_counter("cams_db_errors_total", {
                'operation': 'execute_query',
                'error_type': e.__class__.__name__
            })
            raise

    @db_operation("execute_query_fetchone")
    def execute_query_fetchone(self, query, params=None):
        """
        Executes a query expected to return a single row (e.g., SELECT by primary key).
        Returns a dictionary representing the row, or None if not found.
        """
        logger.debug("Executing fetchone query", extra={
            'query': query,
            'params': str(params)[:500]  # Truncate long parameters
        })
        
        try:
            # In a real implementation, this would interact with the database.
            # For pseudo-code, this is highly conceptual.
            if "SELECT" in query and "aiAgentAddress" in query and params:
                metrics.increment_counter("cams_db_select_total", {"table": "agent_mappings"})
                # Simulate finding a record for demonstration if it's a getAgentMapping call
                if params[0] == "agent123@example.com":
                    result = {
                        "aiAgentAddress": params[0],
                        "inboxDestinationType": "GCP_PUBSUB_TOPIC",
                        "inboxName": "projects/your-gcp-project/topics/agent123-inbox",
                        "status": "ACTIVE",
                        "lastHealthCheckTimestamp": None,
                        "registrationTimestamp": datetime.datetime.now(datetime.timezone.utc),
                        "lastUpdatedTimestamp": datetime.datetime.now(datetime.timezone.utc),
                        "updatedBy": "system",
                        "description": "Sample agent",
                        "ownerTeam": "Alpha Team"
                }
        return None

# Initialize database client with error handling
try:
    db_client = DBClient()
    logger.info("Database client initialized successfully")
except Exception as e:
    logger.critical("Failed to initialize database client", exc_info=True)
    raise

# --- CAMS API Operations ---

def registerAgentMapping(aiAgentAddress: str, inboxDestinationType: str, inboxName: str,
                         description: str = None, ownerTeam: str = None, updatedBy: str = None):
    """
    Creates a new agent mapping record. Status defaults to ACTIVE.
    lastUpdatedTimestamp and registrationTimestamp are handled by the database.
    """
    operation = "register_agent_mapping"
    logger.info(f"Starting {operation}", extra={
        'ai_agent_address': aiAgentAddress,
        'inbox_destination_type': inboxDestinationType,
        'operation': operation
    })
    
    start_time = time.time()
    status = 'success'
    
    try:
        # Input validation
        if not all([aiAgentAddress, inboxDestinationType, inboxName]):
            error_msg = "Missing required fields"
            logger.error(error_msg, extra={
                'ai_agent_address': aiAgentAddress,
                'missing_fields': [
                    field for field, value in [
                        ('aiAgentAddress', aiAgentAddress),
                        ('inboxDestinationType', inboxDestinationType),
                        ('inboxName', inboxName)
                    ] if not value
                ]
            })
            metrics.increment_counter("cams_validation_errors_total", {
                'operation': operation,
                'error_type': 'missing_required_fields'
            })
            raise ValueError(error_msg)
        
        # Check if agent already exists
        existing_agent = getAgentMapping(aiAgentAddress)
        if existing_agent:
            error_msg = f"Agent with address '{aiAgentAddress}' already exists"
            logger.warning(error_msg, extra={'ai_agent_address': aiAgentAddress})
            metrics.increment_counter("cams_validation_errors_total", {
                'operation': operation,
                'error_type': 'agent_already_exists'
            })
            raise ValueError(f"Error: {error_msg}.")

        # Construct the INSERT query
        query = """
        INSERT INTO agent_mappings 
        (aiAgentAddress, inboxDestinationType, inboxName, status, description, ownerTeam, updatedBy)
        VALUES (?, ?, ?, 'ACTIVE', ?, ?, ?)
        """
        
        logger.debug("Executing agent registration query", extra={
            'ai_agent_address': aiAgentAddress,
            'inbox_destination_type': inboxDestinationType
        })
        
        # Execute the query
        success = db_client.execute_query(
            query,
            (aiAgentAddress, inboxDestinationType, inboxName, 
             description, ownerTeam, updatedBy or "system")
        )
        
        if not success:
            error_msg = "Failed to register agent in database"
            logger.error(error_msg, extra={'ai_agent_address': aiAgentAddress})
            metrics.increment_counter("cams_operation_errors_total", {
                'operation': operation,
                'error_type': 'database_error'
            })
            raise RuntimeError(error_msg)
            
        logger.info("Agent registered successfully", extra={
            'ai_agent_address': aiAgentAddress,
            'inbox_destination_type': inboxDestinationType
        })
        metrics.increment_counter("cams_operations_total", {
            'operation': 'register_agent',
            'status': 'success'
        })
        
        # Return the newly created agent mapping
        return getAgentMapping(aiAgentAddress)
        
                "aiAgentAddress": aiAgentAddress,
                "inboxDestinationType": inboxDestinationType,
                "inboxName": inboxName,
                "status": "ACTIVE",
                "description": description,
                "ownerTeam": ownerTeam,
                "updatedBy": updatedBy
                # Timestamps would be set by DB
            }
        else:
            print(f"Failed to register agent mapping for {aiAgentAddress}")
            return False
    except Exception as e:
        print(f"Error during agent registration: {e}")
        # In a real app, re-raise a custom exception or handle appropriately
        raise

def getAgentMapping(aiAgentAddress: str):
    """
    Retrieves a single agent mapping record by its aiAgentAddress.
    Returns the full agent mapping record (dictionary/object) or None if not found.
    """
    operation = "get_agent_mapping"
    logger.info(f"Starting {operation}", extra={
        'ai_agent_address': aiAgentAddress,
        'operation': operation
    })
    
    start_time = time.time()
    status = 'success'
    
    try:
        # Input validation
        if not aiAgentAddress:
            error_msg = "aiAgentAddress is required"
            logger.error(error_msg, extra={'operation': operation})
            metrics.increment_counter("cams_validation_errors_total", {
                'operation': operation,
                'error_type': 'missing_required_field'
            })
            raise ValueError(f"{error_msg}.")

        # This would be a parameterized query in a real implementation
        query = """
            SELECT * FROM agent_mappings 
            WHERE aiAgentAddress = %s
        """
        
        logger.debug("Executing agent lookup query", extra={
            'ai_agent_address': aiAgentAddress
        })
        
        try:
            row = db_client.execute_query_fetchone(query, (aiAgentAddress,))
            if row:
                logger.info("Agent mapping found", extra={
                    'ai_agent_address': aiAgentAddress,
                    'status': row.get('status')
                })
                metrics.increment_counter("cams_lookups_total", {
                    'status': 'found',
                    'agent_status': row.get('status', 'UNKNOWN')
                })
                return row
            else:
                logger.info("Agent mapping not found", extra={
                    'ai_agent_address': aiAgentAddress
                })
                metrics.increment_counter("cams_lookups_total", {
                    'status': 'not_found'
                })
                return None
                
        except Exception as e:
            error_msg = f"Database error while retrieving agent mapping"
            logger.error(error_msg, extra={
                'ai_agent_address': aiAgentAddress,
                'error': str(e),
                'error_type': e.__class__.__name__
            }, exc_info=True)
            metrics.increment_counter("cams_operation_errors_total", {
                'operation': operation,
                'error_type': 'database_error'
            })
            raise RuntimeError(f"{error_msg}: {e}")
            
    except Exception as e:
        status = 'error'
        error_type = e.__class__.__name__
        logger.error(f"{operation} failed", exc_info=True, extra={
            'ai_agent_address': aiAgentAddress,
            'error': str(e),
            'error_type': error_type
        })
        metrics.increment_counter("cams_operations_total", {
            'operation': operation,
            'status': 'error',
            'error_type': error_type
        })
        raise
    finally:
        duration = time.time() - start_time
        metrics.record_latency(
            "cams_operation_duration_seconds",
            duration,
            {'operation': operation, 'status': status}
        )
        logger.info(f"{operation} completed", extra={
            'ai_agent_address': aiAgentAddress,
            'duration_seconds': duration,
            'status': status
        })

def updateAgentStatus(aiAgentAddress: str, newStatus: str, updatedBy: str = None):
    """
    Updates only the status field for a given agent.
    Also updates lastUpdatedTimestamp (handled by DB trigger) and updatedBy.
    """
    operation = "update_agent_status"
    logger.info(f"Starting {operation}", extra={
        'ai_agent_address': aiAgentAddress,
        'new_status': newStatus,
        'operation': operation
    })
    
    start_time = time.time()
    status = 'success'
    
    try:
        # Input validation
        if not all([aiAgentAddress, newStatus]):
            error_msg = "aiAgentAddress and newStatus are required"
            logger.error(error_msg, extra={
                'operation': operation,
                'missing_fields': [
                    field for field, value in [
                        ('aiAgentAddress', aiAgentAddress),
                        ('newStatus', newStatus)
                    ] if not value
                ]
            })
            metrics.increment_counter("cams_validation_errors_total", {
                'operation': operation,
                'error_type': 'missing_required_fields'
            })
            raise ValueError(f"{error_msg}.")
        
        # Validate status value (conceptual - in real code, use an enum)
        valid_statuses = ["ACTIVE", "INACTIVE", "SUSPENDED"]
        if newStatus not in valid_statuses:
            error_msg = f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            logger.error(error_msg, extra={
                'operation': operation,
                'provided_status': newStatus,
                'valid_statuses': valid_statuses
            })
            metrics.increment_counter("cams_validation_errors_total", {
                'operation': operation,
                'error_type': 'invalid_status'
            })
            raise ValueError(error_msg)

        # Check if agent exists first
        existing_agent = getAgentMapping(aiAgentAddress)
        if not existing_agent:
            error_msg = f"Agent with address '{aiAgentAddress}' not found"
            logger.warning(error_msg, extra={'ai_agent_address': aiAgentAddress})
            metrics.increment_counter("cams_validation_errors_total", {
                'operation': operation,
                'error_type': 'agent_not_found'
            })
            raise ValueError(f"{error_msg}.")

        # Don't update if status hasn't changed
        current_status = existing_agent.get('status')
        if current_status == newStatus:
            logger.info("Status unchanged, skipping update", extra={
                'ai_agent_address': aiAgentAddress,
                'current_status': current_status,
                'new_status': newStatus
            })
            return existing_agent

        # Construct the UPDATE query
        query = """
            UPDATE agent_mappings 
            SET status = %s, 
                updatedBy = %s,
                lastUpdatedTimestamp = CURRENT_TIMESTAMP
            WHERE aiAgentAddress = %s
        """
        params = (newStatus, updatedBy or "system", aiAgentAddress)
        
        logger.debug("Executing status update query", extra={
            'ai_agent_address': aiAgentAddress,
            'new_status': newStatus,
            'previous_status': current_status
        })
        
        try:
            success = db_client.execute_query(query, params)
            if not success:
                error_msg = f"Failed to update status for agent {aiAgentAddress}"
                logger.error(error_msg, extra={'ai_agent_address': aiAgentAddress})
                metrics.increment_counter("cams_operation_errors_total", {
                    'operation': operation,
                    'error_type': 'database_error'
                })
                raise RuntimeError(error_msg)
                
            logger.info("Agent status updated successfully", extra={
                'ai_agent_address': aiAgentAddress,
                'previous_status': current_status,
                'new_status': newStatus
            })
            metrics.increment_counter("cams_status_updates_total", {
                'previous_status': current_status,
                'new_status': newStatus
            })
            
            # Return the updated record
            return getAgentMapping(aiAgentAddress)
            
        except Exception as e:
            error_msg = f"Database error while updating agent status"
            logger.error(error_msg, extra={
                'ai_agent_address': aiAgentAddress,
                'error': str(e),
                'error_type': e.__class__.__name__
            }, exc_info=True)
            metrics.increment_counter("cams_operation_errors_total", {
                'operation': operation,
                'error_type': 'database_error'
            })
            raise RuntimeError(f"{error_msg}: {e}")
            
    except Exception as e:
        status = 'error'
        error_type = e.__class__.__name__
        logger.error(f"{operation} failed", exc_info=True, extra={
            'ai_agent_address': aiAgentAddress,
            'error': str(e),
            'error_type': error_type
        })
        metrics.increment_counter("cams_operations_total", {
            'operation': operation,
            'status': 'error',
            'error_type': error_type
        })
        raise
    finally:
        duration = time.time() - start_time
        metrics.record_latency(
            "cams_operation_duration_seconds",
            duration,
            {'operation': operation, 'status': status}
        )
        logger.info(f"{operation} completed", extra={
            'ai_agent_address': aiAgentAddress,
            'duration_seconds': duration,
            'status': status
        })


def updateAgentMappingDetails(aiAgentAddress: str, updatedBy: str = None, **kwargs):
    """
    Update multiple fields of an agent mapping record.
    
    Args:
        aiAgentAddress: The unique identifier of the agent.
        updatedBy: Identifier of who is making the update.
        **kwargs: Key-value pairs of fields to update.
        
    Returns:
        The updated agent mapping record, or None if the agent was not found.
        
    Note:
        - Special handling for health check updates to ensure proper timestamp and logging.
    """
    allowed_fields = {
        'inboxDestinationType', 'inboxName', 'status', 'description', 
        'ownerTeam', 'lastHealthCheckTimestamp', 'healthCheckDetails'
    }

    try:
        success = db_client.execute_query(query, tuple(params))
        if success: # In a real scenario, this would check affected_rows > 0
            print(f"Details updated for agent {aiAgentAddress} with fields: {kwargs}")
            # For pseudo-code, fetch and return the updated record
            # In a real implementation, the DB might return the updated row, or we'd re-fetch.
            updated_record = getAgentMapping(aiAgentAddress) # Re-fetch to get all fields including timestamps

            # Simulate the timestamp update for the returned object if getAgentMapping mock isn't perfect
            if updated_record:
                # The mock for getAgentMapping might not be sophisticated enough to reflect partial updates immediately
                # So, we manually merge the changes into what it might return for this pseudo call
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        updated_record[key] = value
                
                # Update timestamps
                current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                updated_record["lastUpdatedTimestamp"] = current_time
                
                # If this is a health check update, ensure the timestamp is set
                if 'lastHealthCheckTimestamp' not in kwargs and any(field in kwargs for field in ['status', 'healthCheckDetails']):
                    updated_record["lastHealthCheckTimestamp"] = current_time
                
                updated_record["updatedBy"] = updatedBy or 'system'
                
                # Log health check updates
                if 'status' in kwargs or 'healthCheckDetails' in kwargs:
                    logger.info(
                        "Agent health status updated",
                        extra={
                            'ai_agent_address': aiAgentAddress,
                            'new_status': kwargs.get('status'),
                            'details': kwargs.get('healthCheckDetails', ''),
                            'updated_by': updatedBy or 'system'
                        }
                    )
                
                return updated_record
            return None # Should not happen if update was successful and agent existed
        else:
            # This could mean agent not found by the UPDATE query itself, or no actual change made
            print(f"Agent {aiAgentAddress} not found or details not updated.")
            return None
    except Exception as e:
        print(f"Error updating agent details for {aiAgentAddress}: {e}")
        raise

# --- Example Usage (Conceptual) ---
if __name__ == "__main__":
    print("CAMS API Pseudo-code demonstrations:")

    # Registration
    print("\n--- Attempting Registration ---")
    try:
        new_agent = registerAgentMapping(
            aiAgentAddress="agent007@example.com",
            inboxDestinationType="GCP_PUBSUB_TOPIC",
            inboxName="projects/your-gcp-project/topics/agent007-inbox",
            description="Top Secret Agent",
            ownerTeam="MI6",
            updatedBy="Q"
        )
        if new_agent:
            print(f"Registered: {new_agent}")
    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"Registration failed: {e}")

    # Simulate already exists for next registration attempt by "finding" it
    db_client.execute_query_fetchone = lambda q, p: {"aiAgentAddress": p[0]} if p[0] == "agent007@example.com" else None

    print("\n--- Attempting Duplicate Registration ---")
    try:
        registerAgentMapping(
            aiAgentAddress="agent007@example.com", # Duplicate
            inboxDestinationType="GCP_PUBSUB_TOPIC",
            inboxName="projects/your-gcp-project/topics/agent007-inbox-v2",
            description="Top Secret Agent - new inbox",
            ownerTeam="MI6",
            updatedBy="Q"
        )
    except ValueError as ve:
        print(ve) # Expected: "Error: Agent with address 'agent007@example.com' already exists."


    # Get Agent Mapping
    print("\n--- Attempting Get Agent Mapping ---")
    # Restore more complete mock for getAgentMapping
    def mock_get(query, params):
        if params[0] == "agent123@example.com":
            return {
                "aiAgentAddress": params[0], "inboxDestinationType": "GCP_PUBSUB_TOPIC",
                "inboxName": "projects/your-gcp-project/topics/agent123-inbox", "status": "ACTIVE",
                # ... other fields
            }
        return None
    db_client.execute_query_fetchone = mock_get

    agent_details = getAgentMapping("agent123@example.com")
    if agent_details:
        print(f"Retrieved: {agent_details}")

    agent_details_nonexistent = getAgentMapping("nonexistent@example.com")
    if not agent_details_nonexistent:
        print("Correctly returned None for non-existent agent.")

    # Update Agent Status
    print("\n--- Attempting Update Agent Status ---")
    # Assume agent123 exists for update operations for this pseudo-code
    # The db_client.execute_query will return True based on its simplified logic
    if updateAgentStatus("agent123@example.com", "INACTIVE", updatedBy="OpsTeam"):
        print("Status update call succeeded (pseudo).")
        # To verify, one would typically call getAgentMapping again.
        # For pseudo-code, we assume the underlying db_client.execute_query indicates success.

    try:
        updateAgentStatus("agent123@example.com", "INVALID_STATUS", updatedBy="OpsTeam")
    except ValueError as ve:
        print(f"Caught expected error for invalid status: {ve}")


    # Update Agent Inbox
    print("\n--- Attempting Update Agent Inbox ---")
    if updateAgentInbox("agent123@example.com", "GCP_PUBSUB_TOPIC_NEW", "projects/new-project/topics/new-inbox", updatedBy="DevTeam"):
        print("Inbox update call succeeded (pseudo).")

    # Update Agent Mapping Details (New Generic Function)
    print("\n--- Attempting Update Agent Mapping Details (Generic) ---")
    # First, ensure the agent exists for the update context
    db_client.execute_query_fetchone = lambda q, p: {
        "aiAgentAddress": p[0], "inboxDestinationType": "GCP_PUBSUB_TOPIC",
        "inboxName": "projects/your-gcp-project/topics/agent123-inbox", "status": "ACTIVE",
        "description": "Original Description", "ownerTeam": "Alpha Team",
        "registrationTimestamp": datetime.datetime.now(datetime.timezone.utc),
        "lastUpdatedTimestamp": datetime.datetime.now(datetime.timezone.utc)
    } if p[0] == "agent123@example.com" else None

    updated_details = updateAgentMappingDetails(
        aiAgentAddress="agent123@example.com",
        updatedBy="ConfigMgmt",
        description="Updated description via generic method",
        ownerTeam="Bravo Team",
        status="INACTIVE"
    )
    if updated_details:
        print(f"Generic update call succeeded. Details: {updated_details}")
        # Verify the conceptual lastUpdatedTimestamp would have changed
        # In a real system, we'd fetch again or check returned data.
        # Here, the returned dict includes a new timestamp.

    # Test generic update for a non-existent agent
    print("\n--- Attempting Update Agent Mapping Details for Non-existent Agent ---")
    non_existent_updated = updateAgentMappingDetails(
        aiAgentAddress="nonexistent-for-update@example.com",
        description="This should not apply"
    )
    if not non_existent_updated:
        print("Correctly failed to update non-existent agent with generic method.")

    # Restore mock_get for subsequent tests if any rely on specific behavior
    def mock_get_restore(query, params):
        if params[0] == "agent123@example.com": # This agent might have been "deleted" in conceptual tests below
            return {
                "aiAgentAddress": params[0], "inboxDestinationType": "GCP_PUBSUB_TOPIC_NEW", # from previous update
                "inboxName": "projects/new-project/topics/new-inbox", "status": "INACTIVE", # from generic update
                "description": "Updated description via generic method", "ownerTeam": "Bravo Team",
            }
        return None
    db_client.execute_query_fetchone = mock_get_restore


    # Delete Agent Mapping
    print("\n--- Attempting Delete Agent Mapping ---")
    if deleteAgentMapping("agent123@example.com"):
        print("Delete call succeeded (pseudo).")
        # To verify, one would typically call getAgentMapping and expect None.
        # For pseudo-code, we assume the underlying db_client.execute_query indicates success.

    print("\n--- CAMS API Pseudo-code demonstrations complete. ---")
