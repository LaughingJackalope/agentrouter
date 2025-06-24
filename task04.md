# Jules Task 04: Implement Message Ingestion API (Router Service)

## 1. Task Objective

This task is to implement the core Message Ingestion API (`POST /v1/messages`) within the Message Router Service. This service will be responsible for:
1.  Receiving incoming messages via its API endpoint.
2.  Generating a unique `messageId`.
3.  Validating the incoming request payload.
4.  Looking up the `aiAgentAddress` in the Central Agent Mapping Service (CAMS).
5.  Transforming the message into the Pub/Sub schema format.
6.  Publishing the transformed message to the appropriate Google Pub/Sub topic.
7.  Returning an immediate `202 Accepted` response to the sender.

This aligns with **Phase 1: Core Routing MVP**, specifically **"Implement Message Ingestion API (Router Service)"** in our Pragmatic Development Roadmap.

## 2. Context & Rationale

The Message Router Service is the primary entry point for all systems wishing to send messages to AI Agents. It acts as the central orchestrator, leveraging the Pub/Sub schema defined in Task 01 and interacting with the CAMS implemented in Task 02. Its efficiency and reliability are paramount for the overall system.

## 3. Detailed Requirements

### 3.1. API Endpoint and Responses

* **Endpoint:** `POST /v1/messages`
* **Request Payload Structure:**
    ```json
    {
      "aiAgentAddress": "string",             // REQUIRED. e.g., "agent-sales@yourorg.com"
      "payload": {},                        // REQUIRED. JSON object for the AI Agent.
      "senderMetadata": {                   // OPTIONAL.
        "serviceName": "string",            // e.g., "CRM_System"
        "correlationId": "string",          // Sender-specific correlation ID.
        "senderProvidedMessageId": "string" // OPTIONAL. Sender's own message ID.
      }
    }
    ```
* **Successful Response:**
    * **HTTP Status:** `202 Accepted`
    * **Response Body (JSON):**
        ```json
        {
          "messageId": "mrc-generated-uuid-12345" // The unique ID assigned to the message by the Router.
        }
        ```

### 3.2. Core Logic Flow

Jules should implement the core logic for the `POST /v1/messages` handler (e.g., a function `handle_message_ingestion(request_payload)`):

1.  **Receive Request:** Accept the incoming JSON `request_payload`.
2.  **Generate `messageId`:** Generate a new, unique UUID for this message. This will be the `messageId` for the Pub/Sub attributes and the API response.
3.  **Input Validation:**
    * Ensure `aiAgentAddress` and `payload` are present in the `request_payload`.
    * Basic format validation for `aiAgentAddress` (e.g., non-empty string).
    * If validation fails, return an appropriate HTTP error response (e.g., `400 Bad Request`).
4.  **CAMS Lookup:**
    * Call the CAMS `getAgentMapping(aiAgentAddress)` function (from Task 02's output) using the `aiAgentAddress` from the request.
    * Assume a CAMS client is available (e.g., `cams_client.get_agent_mapping`).
5.  **Conditional Routing Logic:**
    * **Scenario A: Agent Not Found in CAMS:**
        * If `getAgentMapping` returns `None` (agent address not found), log this event.
        * Return `404 Not Found` HTTP status with an appropriate error message (e.g., "AI Agent Address not found").
    * **Scenario B: Agent Found but `status` is `INACTIVE`:**
        * If `getAgentMapping` returns a record but its `status` field is `'INACTIVE'`, log this event.
        * Return `404 Not Found` HTTP status with an appropriate error message (e.g., "AI Agent is currently inactive").
    * **Scenario C: Agent Found and `status` is `ACTIVE`:**
        * **Transform to Pub/Sub Message:** Use the logic and schema defined in **Jules Task 01** (`pubsub_message_schema.json` and `schemas/pubsub/README.md`) to transform the `request_payload` into the Pub/Sub message format. Ensure the generated `messageId` is used.
        * **Publish to Pub/Sub:** Publish the transformed message to the Pub/Sub topic identified by `inboxName` from the CAMS lookup result.
        * Assume a Pub/Sub client is available (e.g., `pubsub_publisher.publish_message`).
        * **Error Handling for Pub/Sub Publish:** If the Pub/Sub publish operation fails (e.g., network error, permission issue), log the error and return an appropriate HTTP error response (e.g., `500 Internal Server Error`). Do not return `202 Accepted` in this case.
6.  **Return Success:** If the message is successfully published to Pub/Sub, return `202 Accepted` with the generated `messageId` in the response body.

### 3.3. Error Handling Principles

* Use appropriate HTTP status codes (`400`, `404`, `500`).
* Error responses should ideally follow a consistent format (e.g., simple JSON with `error_code` and `message`).

### 3.4. Technology Stack / Language

* The implementation should be in **Python**.
* Assume the use of standard Python libraries for HTTP request handling (e.g., Flask or FastAPI for the API framework, though Jules should only provide the core logic, not the full framework setup unless explicitly simple).
* Assume conceptual clients for CAMS (`cams_client`) and Pub/Sub (`pubsub_publisher`).

## 4. Dependencies

* **Jules Task 01 Output:** Pub/Sub Message Schema (`pubsub_message_schema.json`) and mapping logic (`schemas/pubsub/README.md`).
* **Jules Task 02 Output:** CAMS Core API and persistence interface (`services/cams/`).

## 5. Expected Output from Jules

Upon completion, Jules should provide:

* A Python file (e.g., `message_router_service.py`) containing:
    * The core `POST /v1/messages` handler logic.
    * Stub/placeholder implementations for `cams_client` and `pubsub_publisher` interactions, indicating where those integrations would occur.
    * Input validation and conditional routing logic.
    * Error handling.
* A `README.md` file within the output directory explaining the implementation, the core logic flow, and assumptions.

## 6. Output Location

Please place all output files for this task in a new directory named `services/router/` within the repository root.

---

This task will bring our core message routing pipeline online. Let me know if it's clear for Jules, Pilot!
