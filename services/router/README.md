# Agent Management API (/v1/agent-inboxes)

This document describes the RESTful APIs for managing AI Agent addresses and their associated mappings within the Central Agent Mapping Service (CAMS). These APIs are exposed under the base path `/v1/agent-inboxes`.

The API handlers are implemented in `agent_management_api.py` and interact with a CAMS client (conceptually represented by `cams_client` in the implementation, based on `services/cams/cams_api_pseudo.py`).

## API Endpoints

### 1. Register Agent Mapping (Create)

*   **Endpoint:** `POST /v1/agent-inboxes`
*   **Purpose:** Registers a new AI Agent address and its associated inbox details.
*   **Request Payload (JSON):**
    ```json
    {
      "aiAgentAddress": "string",             // REQUIRED. Unique identifier for the agent.
      "inboxDestinationType": "string",       // REQUIRED. E.g., "GCP_PUBSUB_TOPIC".
      "inboxName": "string",                  // REQUIRED. The actual Pub/Sub topic name or other destination.
      "description": "string",                // OPTIONAL.
      "ownerTeam": "string"                   // OPTIONAL.
    }
    ```
*   **Successful Response:**
    *   **HTTP Status:** `201 Created`
    *   **Response Body (JSON):** The newly created agent mapping record, including generated timestamps and default status (`ACTIVE`).
        ```json
        {
          "aiAgentAddress": "agent-new@example.com",
          "inboxDestinationType": "GCP_PUBSUB_TOPIC",
          "inboxName": "projects/your-gcp-project/topics/agent-new-inbox",
          "status": "ACTIVE",
          "registrationTimestamp": "YYYY-MM-DDTHH:MM:SS.sssZ", // Example: "2025-06-24T10:00:00.000Z"
          "lastUpdatedTimestamp": "YYYY-MM-DDTHH:MM:SS.sssZ",  // Example: "2025-06-24T10:00:00.000Z"
          "description": "New agent for customer support",    // If provided
          "ownerTeam": "Support-A",                         // If provided
          "updatedBy": "router_service"                     // Or as set by CAMS
        }
        ```
*   **Error Handling:**
    *   `400 Bad Request`: For invalid input (missing required fields, invalid JSON).
    *   `409 Conflict`: If `aiAgentAddress` already exists.
    *   `500 Internal Server Error`: For unexpected errors during processing.

### 2. Retrieve Agent Mapping (Read)

*   **Endpoint:** `GET /v1/agent-inboxes/{aiAgentAddress}`
*   **Purpose:** Retrieves the details of a specific AI Agent mapping.
*   **Path Parameter:** `{aiAgentAddress}` (e.g., `agent-sales@yourorg.com`)
*   **Successful Response:**
    *   **HTTP Status:** `200 OK`
    *   **Response Body (JSON):** The full agent mapping record.
        ```json
        {
          "aiAgentAddress": "agent-sales@yourorg.com",
          "inboxDestinationType": "GCP_PUBSUB_TOPIC",
          "inboxName": "projects/your-gcp-project/topics/agent-sales-inbox",
          "status": "ACTIVE",
          "registrationTimestamp": "YYYY-MM-DDTHH:MM:SS.sssZ",
          "lastUpdatedTimestamp": "YYYY-MM-DDTHH:MM:SS.sssZ",
          "description": "Sales agent",
          "ownerTeam": "Sales Team"
          // other fields as returned by CAMS client like 'updatedBy', 'lastHealthCheckTimestamp'
        }
        ```
*   **Error Handling:**
    *   `400 Bad Request`: If `aiAgentAddress` path parameter is missing or invalid.
    *   `404 Not Found`: If `aiAgentAddress` does not exist.
    *   `500 Internal Server Error`: For unexpected errors.

### 3. Update Agent Mapping (Update)

*   **Endpoint:** `PUT /v1/agent-inboxes/{aiAgentAddress}`
*   **Purpose:** Updates existing fields for an AI Agent mapping.
*   **Path Parameter:** `{aiAgentAddress}`
*   **Request Payload (JSON):** (All fields are optional. Only provided fields that are supported for update will be changed.)
    ```json
    {
      "inboxDestinationType": "string",       // OPTIONAL
      "inboxName": "string",                  // OPTIONAL
      // "description": "string",             // OPTIONAL - Currently NOT directly updatable via this endpoint due to CAMS client pseudo-code limitations
      // "ownerTeam": "string",               // OPTIONAL - Currently NOT directly updatable via this endpoint due to CAMS client pseudo-code limitations
      "status": "string"                      // OPTIONAL (must be "ACTIVE" or "INACTIVE")
    }
    ```
    **Note on Updates:**
    *   This endpoint now supports partial updates for `inboxDestinationType`, `inboxName`, `description`, `ownerTeam`, and `status`.
    *   Only the fields provided in the request body will be targeted for update.
    *   If `status` is provided, it must be either `"ACTIVE"` or `"INACTIVE"`.
    *   The API handler calls the `cams_client.updateAgentMappingDetails` function internally.

*   **Successful Response:**
    *   **HTTP Status:** `200 OK`
    *   **Response Body (JSON):** The updated agent mapping record.
*   **Error Handling:**
    *   `400 Bad Request`: For invalid input (e.g., invalid `status` value, missing `inboxName` if `inboxDestinationType` is provided for update without an existing value).
    *   `404 Not Found`: If `aiAgentAddress` does not exist.
    *   `500 Internal Server Error`: For unexpected errors during update.

### 4. Delete Agent Mapping (Delete)

*   **Endpoint:** `DELETE /v1/agent-inboxes/{aiAgentAddress}`
*   **Purpose:** Deletes an AI Agent mapping record.
*   **Path Parameter:** `{aiAgentAddress}`
*   **Successful Response:**
    *   **HTTP Status:** `204 No Content`
*   **Error Handling:**
    *   `400 Bad Request`: If `aiAgentAddress` path parameter is missing or invalid.
    *   `404 Not Found`: If `aiAgentAddress` does not exist.
    *   `500 Internal Server Error`: For unexpected errors during deletion.

## Interaction with CAMS Client

The API handlers in `agent_management_api.py` use a conceptual `cams_client` to perform operations on the CAMS data store. The methods of this client are assumed to be:

*   `cams_client.registerAgentMapping(aiAgentAddress, inboxDestinationType, inboxName, description=None, ownerTeam=None)`: Registers a new agent.
*   `cams_client.getAgentMapping(aiAgentAddress)`: Retrieves an agent's details.
*   `cams_client.updateAgentMappingDetails(aiAgentAddress, updatedBy=None, **kwargs)`: Updates one or more fields of an existing agent mapping (used by the `PUT` endpoint).
*   `cams_client.deleteAgentMapping(aiAgentAddress)`: Deletes an agent mapping.
*   The CAMS client also has older specific update functions like `updateAgentStatus` and `updateAgentInbox`, but the `PUT` endpoint for agent management now uses the more generic `updateAgentMappingDetails`.

Errors from the CAMS client (e.g., agent not found, duplicate agent, invalid input for updates) are mapped to appropriate HTTP status codes by the API handlers. The `updatedBy` field in CAMS records is generally set by the CAMS client or the API handler (e.g., "router_service/PUT").

---
This README describes the Agent Management APIs. For details on the Message Ingestion API (`POST /v1/messages`), please refer to `message_router_service_README.md`.
