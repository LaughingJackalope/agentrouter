# services/cams/cams_api_pseudo.py
# Pseudo-code for Central Agent Mapping Service (CAMS) Core API Operations

import datetime

# Conceptual Database Client
# This is a placeholder for whatever database interaction library/ORM will be used.
# It's assumed that this client handles connection management and sanitizes inputs
# to prevent SQL injection if raw SQL is being constructed.

class DBClient:
    def execute_query(self, query, params=None):
        """
        Executes a query that modifies data (INSERT, UPDATE, DELETE)
        or a query that might return multiple rows (though not used for that here).
        Returns True for success/row affected, False otherwise, or raises an exception.
        """
        print(f"Executing Query: {query} with Params: {params}")
        # In a real implementation, this would interact with the database.
        # For pseudo-code, we'll assume success if params seem valid for the operation.
        if "INSERT" in query and params and len(params) >= 3: # Basic check for register
            return True
        if "UPDATE" in query and params and len(params) >= 2: # Basic check for update
            return True
        if "DELETE" in query and params and len(params) >=1: # Basic check for delete
            return True
        return False

    def execute_query_fetchone(self, query, params=None):
        """
        Executes a query expected to return a single row (e.g., SELECT by primary key).
        Returns a dictionary representing the row, or None if not found.
        """
        print(f"Executing Query (fetchone): {query} with Params: {params}")
        # In a real implementation, this would interact with the database.
        # For pseudo-code, this is highly conceptual.
        if "SELECT" in query and "aiAgentAddress" in query and params:
            # Simulate finding a record for demonstration if it's a getAgentMapping call
            if params[0] == "agent123@example.com":
                return {
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

db_client = DBClient() # Instantiate the conceptual client

# --- CAMS API Operations ---

def registerAgentMapping(aiAgentAddress: str, inboxDestinationType: str, inboxName: str,
                         description: str = None, ownerTeam: str = None, updatedBy: str = None):
    """
    Creates a new agent mapping record. Status defaults to ACTIVE.
    lastUpdatedTimestamp and registrationTimestamp are handled by the database.
    """
    if not all([aiAgentAddress, inboxDestinationType, inboxName]):
        raise ValueError("aiAgentAddress, inboxDestinationType, and inboxName are required.")

    # Check for duplicates first (conceptual - real DB would have unique constraint)
    if getAgentMapping(aiAgentAddress):
        raise ValueError(f"Error: Agent with address '{aiAgentAddress}' already exists.")

    query = """
        INSERT INTO agent_inboxes (
            aiAgentAddress, inboxDestinationType, inboxName,
            description, ownerTeam, updatedBy, status
            -- registrationTimestamp and lastUpdatedTimestamp have defaults
            -- status defaults to ACTIVE
        ) VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE');
    """
    params = (aiAgentAddress, inboxDestinationType, inboxName, description, ownerTeam, updatedBy)

    try:
        success = db_client.execute_query(query, params)
        if success:
            print(f"Agent mapping registered for {aiAgentAddress}")
            # Return the data that would have been created (or query it back)
            # For pseudo-code, we can construct it based on input.
            return {
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
    if not aiAgentAddress:
        raise ValueError("aiAgentAddress is required.")

    query = """
        SELECT aiAgentAddress, inboxDestinationType, inboxName, status,
               lastHealthCheckTimestamp, registrationTimestamp, lastUpdatedTimestamp,
               updatedBy, description, ownerTeam
        FROM agent_inboxes
        WHERE aiAgentAddress = %s;
    """
    params = (aiAgentAddress,)
    record = db_client.execute_query_fetchone(query, params)

    if record:
        print(f"Agent mapping found for {aiAgentAddress}")
    else:
        print(f"No agent mapping found for {aiAgentAddress}")
    return record

def updateAgentStatus(aiAgentAddress: str, newStatus: str, updatedBy: str = None):
    """
    Updates only the status field for a given agent.
    Also updates lastUpdatedTimestamp (handled by DB trigger) and updatedBy.
    """
    if not aiAgentAddress:
        raise ValueError("aiAgentAddress is required.")
    if newStatus not in ('ACTIVE', 'INACTIVE'):
        raise ValueError("newStatus must be 'ACTIVE' or 'INACTIVE'.")

    query = """
        UPDATE agent_inboxes
        SET status = %s, updatedBy = %s
        -- lastUpdatedTimestamp is updated by a DB trigger
        WHERE aiAgentAddress = %s;
    """
    params = (newStatus, updatedBy, aiAgentAddress)

    try:
        success = db_client.execute_query(query, params)
        if success:
            print(f"Status updated to {newStatus} for agent {aiAgentAddress}")
        else:
            # This part of pseudo-code might not be reached if db_client always returns True on basic check
            # A real db_client would return affected_rows or similar.
            print(f"Agent {aiAgentAddress} not found or status not updated.")
        return success # Or check affected_rows in a real scenario
    except Exception as e:
        print(f"Error updating agent status: {e}")
        raise

def updateAgentInbox(aiAgentAddress: str, newInboxDestinationType: str, newInboxName: str, updatedBy: str = None):
    """
    Updates the inbox destination details for an agent.
    Also updates lastUpdatedTimestamp (handled by DB trigger) and updatedBy.
    """
    if not all([aiAgentAddress, newInboxDestinationType, newInboxName]):
        raise ValueError("aiAgentAddress, newInboxDestinationType, and newInboxName are required.")

    query = """
        UPDATE agent_inboxes
        SET inboxDestinationType = %s, inboxName = %s, updatedBy = %s
        -- lastUpdatedTimestamp is updated by a DB trigger
        WHERE aiAgentAddress = %s;
    """
    params = (newInboxDestinationType, newInboxName, updatedBy, aiAgentAddress)

    try:
        success = db_client.execute_query(query, params)
        if success:
            print(f"Inbox updated for agent {aiAgentAddress}")
        else:
            print(f"Agent {aiAgentAddress} not found or inbox not updated.")
        return success # Or check affected_rows
    except Exception as e:
        print(f"Error updating agent inbox: {e}")
        raise

def deleteAgentMapping(aiAgentAddress: str):
    """
    Removes an agent mapping record.
    """
    if not aiAgentAddress:
        raise ValueError("aiAgentAddress is required.")

    query = "DELETE FROM agent_inboxes WHERE aiAgentAddress = %s;"
    params = (aiAgentAddress,)

    try:
        success = db_client.execute_query(query, params)
        if success: # In real scenario, check if any row was actually deleted
            print(f"Agent mapping for {aiAgentAddress} deleted.")
        else:
            print(f"Agent {aiAgentAddress} not found or not deleted.")
        return success # Or check affected_rows
    except Exception as e:
        print(f"Error deleting agent mapping: {e}")
        raise

def updateAgentMappingDetails(aiAgentAddress: str, updatedBy: str = None, **kwargs):
    """
    Updates arbitrary fields for a given agent mapping.
    Handles partial updates: only fields present in kwargs are modified.
    Also updates lastUpdatedTimestamp (conceptually handled by DB trigger or ORM) and updatedBy.
    Allowed kwargs keys: "inboxDestinationType", "inboxName", "status", "description", "ownerTeam".
    """
    if not aiAgentAddress:
        raise ValueError("aiAgentAddress is required for update.")
    if not kwargs:
        raise ValueError("No fields provided to update.")

    # Validate status if provided
    if "status" in kwargs and kwargs["status"] not in ('ACTIVE', 'INACTIVE'):
        raise ValueError("Invalid status value. Must be 'ACTIVE' or 'INACTIVE'.")

    # Conceptual: Check if agent exists first
    # In a real DB, an UPDATE query on a non-existent PK might just affect 0 rows.
    # Here, we can use getAgentMapping for a clearer pseudo-code flow.
    existing_mapping = getAgentMapping(aiAgentAddress)
    if not existing_mapping:
        print(f"Agent {aiAgentAddress} not found. Cannot update details.")
        return None # Or raise a specific "NotFound" error

    # Construct the SET part of the SQL query conceptually
    set_clauses = []
    params = []

    allowed_fields = ["inboxDestinationType", "inboxName", "status", "description", "ownerTeam"]

    for key, value in kwargs.items():
        if key in allowed_fields:
            set_clauses.append(f"{key} = %s")
            params.append(value)
        else:
            print(f"Warning: Field '{key}' is not allowed for update and will be ignored.")

    if not set_clauses:
        # This could happen if only disallowed fields were passed in kwargs
        raise ValueError("No valid fields provided for update after filtering.")

    # Add updatedBy to params and query
    set_clauses.append("updatedBy = %s")
    params.append(updatedBy)

    # Conceptually, lastUpdatedTimestamp is also set by the DB
    # set_clauses.append("lastUpdatedTimestamp = CURRENT_TIMESTAMP") # Or similar, handled by DB

    params.append(aiAgentAddress) # For the WHERE clause

    query = f"""
        UPDATE agent_inboxes
        SET {', '.join(set_clauses)}
        WHERE aiAgentAddress = %s;
    """

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
                updated_record["lastUpdatedTimestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                updated_record["updatedBy"] = updatedBy
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
