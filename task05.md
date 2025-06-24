# Jules Task 05: Implement Agent Address Management APIs (CAMS Exposure)

## 1. Task Objective

This task is to implement the external RESTful APIs for managing AI Agent addresses and their associated mappings within the Central Agent Mapping Service (CAMS). These APIs will allow authorized external systems to register, retrieve, update, and deactivate/delete agent mappings.

This aligns with **Phase 2: Management & Operational Readiness**, specifically **"Implement Agent Address Management APIs (CAMS Exposure)"** in our Pragmatic Development Roadmap.

## 2. Context & Rationale

Exposing management APIs for CAMS is crucial for:
* **Centralized Management:** Providing a programmatic way to control the lifecycle of AI Agent addresses.
* **Operational Control:** Enabling teams to onboard new agents or manage existing ones without direct database access.
* **Integration:** Facilitating automated agent registration and deactivation processes.

These APIs will be exposed via the API Gateway, which will handle authentication and authorization.

## 3. Detailed Requirements

Jules should implement the core logic for the following API handlers, which will interact with the CAMS core API (developed in Task 02).

### 3.1. API Endpoints and Payloads

The API endpoints will operate under the base path `/v1/agent-inboxes`.

#### 3.1.1. Register Agent Mapping (Create)

* **Endpoint:** `POST /v1/agent-inboxes`
* **Purpose:** Registers a new AI Agent address and its associated inbox details.
* **Request Payload (JSON):**
    ```json
    {
      "aiAgentAddress": "string",             // REQUIRED. Unique identifier for the agent.
      "inboxDestinationType": "string",       // REQUIRED. E.g., "GCP_PUBSUB_TOPIC".
      "inboxName": "string",                  // REQUIRED. The actual Pub/Sub topic name or other destination.
      "description": "string",                // OPTIONAL.
      "ownerTeam": "string"                   // OPTIONAL.
    }
    ```
* **Successful Response:**
    * **HTTP Status:** `201 Created`
    * **Response Body (JSON):** The newly created agent mapping record (including generated timestamps and default status).
        ```json
        {
          "aiAgentAddress": "agent-new@example.com",
          "inboxDestinationType": "GCP_PUBSUB_TOPIC",
          "inboxName": "projects/your-gcp-project/topics/agent-new-inbox",
          "status": "ACTIVE",
          "registrationTimestamp": "2025-06-24T10:00:00.000Z",
          "lastUpdatedTimestamp": "2025-06-24T10:00:00.000Z",
          "description": "New agent for customer support",
          "ownerTeam": "Support-A"
        }
        ```
* **Error Handling:**
    * `400 Bad Request` for invalid input (missing required fields, invalid format).
    * `409 Conflict` if `aiAgentAddress` already exists.

#### 3.1.2. Retrieve Agent Mapping (Read)

* **Endpoint:** `GET /v1/agent-inboxes/{aiAgentAddress}`
* **Purpose:** Retrieves the details of a specific AI Agent mapping.
* **Path Parameter:** `{aiAgentAddress}` (e.g., `agent-sales@yourorg.com`)
* **Successful Response:**
    * **HTTP Status:** `200 OK`
    * **Response Body (JSON):** The full agent mapping record.
* **Error Handling:**
    * `404 Not Found` if `aiAgentAddress` does not exist.

#### 3.1.3. Update Agent Mapping (Update)

* **Endpoint:** `PUT /v1/agent-inboxes/{aiAgentAddress}`
* **Purpose:** Updates existing fields for an AI Agent mapping (e.g., description, owner, inbox details).
* **Path Parameter:** `{aiAgentAddress}`
* **Request Payload (JSON):** (All fields are optional in request payload, only provided fields will be updated. `aiAgentAddress` in body must match path param if provided.)
    ```json
    {
      "inboxDestinationType": "string",       // OPTIONAL
      "inboxName": "string",                  // OPTIONAL
      "description": "string",                // OPTIONAL
      "ownerTeam": "string",                  // OPTIONAL
      "status": "string"                      // OPTIONAL (e.g., "ACTIVE", "INACTIVE")
    }
    ```
* **Successful Response:**
    * **HTTP Status:** `200 OK`
    * **Response Body (JSON):** The updated agent mapping record.
* **Error Handling:**
    * `400 Bad Request` for invalid input or if `status` value is not `ACTIVE`/`INACTIVE`.
    * `404 Not Found` if `aiAgentAddress` does not exist.

#### 3.1.4. Delete Agent Mapping (Delete)

* **Endpoint:** `DELETE /v1/agent-inboxes/{aiAgentAddress}`
* **Purpose:** Deletes an AI Agent mapping record.
* **Path Parameter:** `{aiAgentAddress}`
* **Successful Response:**
    * **HTTP Status:** `204 No Content`
* **Error Handling:**
    * `404 Not Found` if `aiAgentAddress` does not exist.

### 3.2. Core Logic Implementation

Jules should implement the core handler functions for each of the above API endpoints. These functions will primarily act as wrappers around the CAMS core API functions defined in **Jules Task 02** (e.g., `cams_client.registerAgentMapping`, `cams_client.getAgentMapping`, `cams_client.updateAgentStatus`, `cams_client.deleteAgentMapping`).

* **Validation:** Implement input validation for each API request based on the payload structure.
* **Error Mapping:** Map CAMS client errors (e.g., agent not found, duplicate) to appropriate HTTP error responses.
* **Security Context:** Assume that the API Gateway (upstream) has already handled authentication and authorization. The router service should trust that only authorized requests reach it.

### 3.3. Technology Stack / Language

* Implementation should be in **Python**.
* Assume conceptual clients for CAMS (e.g., `cams_client`).

## 4. Dependencies

* **Jules Task 02 Output:** CAMS Core API and persistence interface (`services/cams/`). This task relies heavily on the CRUD functions defined in Task 02.

## 5. Expected Output from Jules

Upon completion, Jules should provide:

* A Python file (e.g., `agent_management_api.py`) containing the handler logic for all `POST`, `GET`, `PUT`, and `DELETE` operations on `/v1/agent-inboxes`.
* A `README.md` file within the output directory explaining the implemented API endpoints, their expected payloads, and the interaction with the CAMS client.

## 6. Output Location

Please place all output files for this task in the `services/router/` directory (alongside the message ingestion service) within the repository root.

---

This task will give us full programmatic control over agent mappings. Let me know if it's clear, Pilot!
