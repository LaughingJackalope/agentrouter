# Router Service APIs

This document describes the RESTful APIs provided by the Router Service.

## Table of Contents

1. [Agent Management API](#agent-management-api-v1agent-inboxes)
2. [Agent Health Check API](#agent-health-check-api-v1agent-health-check)

## Agent Management API (/v1/agent-inboxes)

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
*   **Purpose:** Deletes an existing AI Agent mapping. In practice, this would likely be a soft delete (marking as INACTIVE) rather than a hard delete.
*   **Path Parameter:** `{aiAgentAddress}` (e.g., `agent-to-delete@yourorg.com`)
*   **Successful Response:**
    *   **HTTP Status:** `204 No Content`
    *   **Response Body:** Empty.
*   **Error Handling:**
    *   `404 Not Found`: If `aiAgentAddress` does not exist.
    *   `500 Internal Server Error`: For unexpected errors during deletion.

## Agent Health Check API (/v1/agent-health)

The Agent Health Check API allows AI Agents to report their health status, which is used to update their status in the Central Agent Mapping Service (CAMS).

### Report Agent Health Status

*   **Endpoint:** `POST /v1/agent-health-check`
*   **Purpose:** Reports the current health status of an AI Agent.
*   **Request Payload (JSON):**
    ```json
    {
      "ai_agent_address": "string",  // REQUIRED. The address of the reporting agent.
      "status": "string",            // REQUIRED. Must be either "HEALTHY" or "UNHEALTHY"
      "details": {                   // OPTIONAL. Additional details about the health status.
        "component": "string",      // Example component name
        "metrics": {}                // Any relevant metrics
      },
      "timestamp": "string"         // OPTIONAL. ISO 8601 timestamp of the health check
    }
    ```
*   **Successful Response:**
    *   **HTTP Status:** `200 OK`
    *   **Response Body (JSON):**
        ```json
        {
          "status": "success",
          "message": "Health status recorded for agent agent@example.com",
          "timestamp": "2025-06-24T12:00:00.000000+00:00"
        }
        ```
*   **Error Handling:**
    *   `400 Bad Request`: For invalid input (missing required fields, invalid status value, etc.)
    *   `404 Not Found`: If the specified agent address is not registered in CAMS.
    *   `500 Internal Server Error`: For unexpected errors during processing.

### Behavior

- When an agent reports as `UNHEALTHY`, it will automatically be marked as `INACTIVE` in CAMS.
- The `last_health_check_timestamp` in CAMS is updated with each health check.
- The health check endpoint is rate-limited and authenticated in production environments.
- All health check events are logged and can be monitored through the system's observability stack.

## Interaction with CAMS Client

The API handlers in `agent_management_api.py` use a conceptual `cams_client` to perform operations on the CAMS data store. The methods of this client are assumed to be:

*   `cams_client.registerAgentMapping(aiAgentAddress, inboxDestinationType, inboxName, description=None, ownerTeam=None)`: Registers a new agent.
*   `cams_client.getAgentMapping(aiAgentAddress)`: Retrieves an agent's details.
*   `cams_client.updateAgentMappingDetails(aiAgentAddress, updatedBy=None, **kwargs)`: Updates one or more fields of an existing agent mapping (used by the `PUT` endpoint).
*   `cams_client.deleteAgentMapping(aiAgentAddress)`: Deletes an agent mapping.
*   The CAMS client also has older specific update functions like `updateAgentStatus` and `updateAgentInbox`, but the `PUT` endpoint for agent management now uses the more generic `updateAgentMappingDetails`.

Errors from the CAMS client (e.g., agent not found, duplicate agent, invalid input for updates) are mapped to appropriate HTTP status codes by the API handlers. The `updatedBy` field in CAMS records is generally set by the CAMS client or the API handler (e.g., "router_service/PUT").

## Notes

*   **Authentication & Authorization:** These endpoints would typically be secured (e.g., using API keys, OAuth 2.0, or IAM) to ensure only authorized services can manage agent mappings and report health status.
*   **Error Responses:** All error responses include a JSON body with an `error` field containing a descriptive message.
*   **Timestamps:** All timestamps are in ISO 8601 format with UTC timezone (e.g., `2025-06-24T10:00:00.000Z`).
*   **Status Values:** The `status` field typically uses `ACTIVE` or `INACTIVE` for agent status, while health checks use `HEALTHY` or `UNHEALTHY`.

## Implementation Notes

*   The API is designed to be RESTful and follows standard HTTP methods and status codes.
*   The implementation uses a conceptual `cams_client` to interact with the Central Agent Mapping Service.
*   Error handling includes input validation and proper error responses.
*   The API is designed to be extensible for future enhancements.
*   Health checks are logged and can be monitored for operational insights.

For more detailed information about the health check API, see [Health Check Guide](./health_check_guide.md).

---
This README describes the Agent Management APIs. For details on the Message Ingestion API (`POST /v1/messages`), please refer to `message_router_service_README.md`.
