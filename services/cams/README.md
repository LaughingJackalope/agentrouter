# Central Agent Mapping Service (CAMS)

This directory contains the core components for the Central Agent Mapping Service (CAMS). CAMS is responsible for mapping `AI Agent Addresses` to their inbox destinations (e.g., Pub/Sub topics) and managing their active status.

## 1. Database Schema (`create_cams_table.sql`)

The database schema for CAMS is defined in `create_cams_table.sql`. It consists of a single table, `agent_inboxes`.

**Target Database:** PostgreSQL

### `agent_inboxes` Table Schema:

| Column                    | Type                     | Constraints                                     | Description                                                                 |
|---------------------------|--------------------------|-------------------------------------------------|-----------------------------------------------------------------------------|
| `aiAgentAddress`          | `VARCHAR(255)`           | `PRIMARY KEY`, `NOT NULL`                       | Unique identifier for an AI Agent.                                          |
| `inboxDestinationType`    | `VARCHAR(50)`            | `NOT NULL`, `DEFAULT 'GCP_PUBSUB_TOPIC'`        | Type of destination (e.g., 'GCP_PUBSUB_TOPIC').                             |
| `inboxName`               | `VARCHAR(255)`           | `NOT NULL`                                      | Name of the Pub/Sub topic or other inbox.                                   |
| `status`                  | `VARCHAR(20)`            | `NOT NULL`, `DEFAULT 'ACTIVE'`, `CHECK (status IN ('ACTIVE', 'INACTIVE'))` | Operational status of the AI Agent ('ACTIVE' or 'INACTIVE').              |
| `lastHealthCheckTimestamp`| `TIMESTAMP WITH TIME ZONE` | (nullable)                                      | Timestamp of the last successful health check (UTC).                        |
| `registrationTimestamp`   | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP`         | Timestamp of when the agent mapping was first registered (UTC).             |
| `lastUpdatedTimestamp`    | `TIMESTAMP WITH TIME ZONE` | `NOT NULL`, `DEFAULT CURRENT_TIMESTAMP`         | Timestamp of the last update to this record (UTC). Auto-updates on modification. |
| `updatedBy`               | `VARCHAR(255)`           | (nullable)                                      | Entity (user or service) that last updated the record.                    |
| `description`             | `TEXT`                   | (nullable)                                      | Human-readable description of the agent.                                    |
| `ownerTeam`               | `VARCHAR(255)`           | (nullable)                                      | Team responsible for managing this AI Agent.                                |

**Automatic Timestamp Updates:**
*   `registrationTimestamp`: Defaults to the current timestamp upon record creation.
*   `lastUpdatedTimestamp`: Defaults to the current timestamp upon record creation and is automatically updated to the current timestamp whenever a record is modified, thanks to a database trigger defined in `create_cams_table.sql`.

## 2. Core API Pseudo-code (`cams_api_pseudo.py`)

The file `cams_api_pseudo.py` provides Python pseudo-code for the core CAMS operations. These functions illustrate the expected interactions with a conceptual database layer (`db_client`).

### Conceptual `DBClient`
The pseudo-code assumes a `DBClient` class with methods like:
*   `execute_query(query, params)`: For `INSERT`, `UPDATE`, `DELETE` operations.
*   `execute_query_fetchone(query, params)`: For `SELECT` operations expected to return a single row.

### API Functions:

*   **`registerAgentMapping(aiAgentAddress: str, inboxDestinationType: str, inboxName: str, description: str = None, ownerTeam: str = None, updatedBy: str = None)`**
    *   **Purpose:** Creates a new agent mapping.
    *   **Inputs:** `aiAgentAddress`, `inboxDestinationType`, `inboxName` are mandatory. `description`, `ownerTeam`, `updatedBy` are optional.
    *   **Output:** A dictionary representing the created record (or relevant parts) on success, or raises an error (e.g., `ValueError` for duplicates).
    *   **Notes:** `status` defaults to `ACTIVE`. `registrationTimestamp` and `lastUpdatedTimestamp` are handled by the database.

*   **`getAgentMapping(aiAgentAddress: str)`**
    *   **Purpose:** Retrieves an agent mapping by `aiAgentAddress`.
    *   **Inputs:** `aiAgentAddress` (string).
    *   **Output:** A dictionary of the agent mapping record or `None` if not found.

*   **`updateAgentStatus(aiAgentAddress: str, newStatus: str, updatedBy: str = None)`**
    *   **Purpose:** Updates the `status` of an agent.
    *   **Inputs:** `aiAgentAddress`, `newStatus` (must be 'ACTIVE' or 'INACTIVE'). `updatedBy` is optional.
    *   **Output:** Boolean indicating success.
    *   **Notes:** Updates `lastUpdatedTimestamp` (via DB trigger) and `updatedBy`.

*   **`updateAgentInbox(aiAgentAddress: str, newInboxDestinationType: str, newInboxName: str, updatedBy: str = None)`**
    *   **Purpose:** Updates an agent's inbox details.
    *   **Inputs:** `aiAgentAddress`, `newInboxDestinationType`, `newInboxName`. `updatedBy` is optional.
    *   **Output:** Boolean indicating success.
    *   **Notes:** Updates `lastUpdatedTimestamp` (via DB trigger) and `updatedBy`.

*   **`updateAgentMappingDetails(aiAgentAddress: str, updatedBy: str = None, **kwargs)`**
    *   **Purpose:** Updates one or more fields of an existing agent mapping. Supports partial updates.
    *   **Inputs:**
        *   `aiAgentAddress` (string, mandatory): The identifier of the agent mapping to update.
        *   `updatedBy` (string, optional): Identifier for the entity performing the update.
        *   `**kwargs`: Keyword arguments where keys are the field names to update (e.g., `description="New description"`, `status="INACTIVE"`).
            *   Allowed fields for update: `inboxDestinationType`, `inboxName`, `status`, `description`, `ownerTeam`.
    *   **Output:** A dictionary of the updated agent mapping record if successful, or `None` if the agent is not found or the update fails. Raises `ValueError` for invalid inputs (e.g. bad status value).
    *   **Notes:**
        *   Updates `lastUpdatedTimestamp` (conceptually via DB trigger or ORM) and `updatedBy`.
        *   If `status` is provided in `kwargs`, it must be one of 'ACTIVE' or 'INACTIVE'.

*   **`deleteAgentMapping(aiAgentAddress: str)`**
    *   **Purpose:** Removes an agent mapping.
    *   **Inputs:** `aiAgentAddress` (string).
    *   **Output:** Boolean indicating success.

### Assumptions:
*   The pseudo-code uses a generic `db_client`. The actual database connection, ORM, and specific SQL dialect nuances for the client will be part of a later implementation.
*   Input sanitization against SQL injection is assumed to be handled by the `db_client` or the underlying database library if raw SQL queries were to be constructed directly (though parameterized queries are shown, which is best practice).
*   The `updatedBy` field is included in relevant functions to track who made changes.

This pseudo-code serves as a blueprint for the actual service implementation. Example usage is provided within an `if __name__ == "__main__":` block in `cams_api_pseudo.py`.
