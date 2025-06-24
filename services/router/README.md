# Message Router Service

This directory contains the implementation for the Message Router Service, specifically the core logic for the `POST /v1/messages` API endpoint.

## 1. Core Logic (`message_router_service.py`)

The `message_router_service.py` file implements the `handle_message_ingestion(request_payload)` function, which is the heart of the message ingestion API.

### Logic Flow:

1.  **Receive Request**: The function accepts an incoming `request_payload` dictionary, which is expected to conform to the API specification:
    ```json
    {
      "aiAgentAddress": "string",
      "payload": {}, // JSON object
      "senderMetadata": { // Optional
        "serviceName": "string",
        "correlationId": "string",
        "senderProvidedMessageId": "string"
      }
    }
    ```

2.  **Generate `messageId`**: A unique UUID (v4) is generated for the incoming message. This ID is used in the Pub/Sub message attributes and returned in the API response.

3.  **Input Validation**:
    *   Checks if `aiAgentAddress` is present, is a non-empty string.
    *   Checks if `payload` is present and is a JSON object.
    *   If validation fails, a `400 Bad Request` response is returned with a JSON error body (e.g., `{"errorCode": "INVALID_REQUEST", "message": "..."}`).

4.  **CAMS Lookup**:
    *   A stubbed `CAMSClient` is used, which internally calls the `getAgentMapping(aiAgentAddress)` function (conceptually from `services.cams.cams_api_pseudo.py`).
    *   This lookup retrieves the agent's details, including their status and Pub/Sub `inboxName`.

5.  **Conditional Routing & Error Handling**:
    *   **Agent Not Found**: If `getAgentMapping` returns `None`, a `404 Not Found` response is returned (`{"errorCode": "AGENT_NOT_FOUND", ...}`).
    *   **Agent Inactive**: If the agent's `status` is `INACTIVE`, a `404 Not Found` response is returned (`{"errorCode": "AGENT_INACTIVE", ...}`).
    *   **Agent Active but `inboxName` Missing**: If the agent is `ACTIVE` but the `inboxName` (Pub/Sub topic) is missing from the CAMS record, a `500 Internal Server Error` is returned (`{"errorCode": "CONFIG_ERROR", ...}`).
    *   **Unknown Agent Status**: If the agent's `status` is neither `ACTIVE` nor `INACTIVE`, a `500 Internal Server Error` is returned.

6.  **Transform to Pub/Sub Message (for Active Agents)**:
    *   The `request_payload.payload` is JSON stringified and then Base64 encoded to form the `data` field of the Pub/Sub message.
    *   The `attributes` field of the Pub/Sub message is populated with:
        *   `messageId` (generated UUID)
        *   `aiAgentAddress` (from the request)
        *   `timestampPublished` (current UTC timestamp in ISO 8601 format)
        *   `contentType` (hardcoded to `"application/json"` for the MVP)
        *   Optional attributes from `request_payload.senderMetadata`: `senderId` (from `serviceName`), `correlationId`, `senderProvidedMessageId`.
    *   If an error occurs during this transformation, a `500 Internal Server Error` is returned (`{"errorCode": "TRANSFORMATION_ERROR", ...}`).

7.  **Publish to Pub/Sub**:
    *   A stubbed `PubSubPublisher` is used. Its `publish_message(topic_name, message_data)` method is called with the `inboxName` from CAMS and the transformed message.
    *   **Error Handling**: If the stubbed publish operation "fails" (simulated via a flag in the stub), a `500 Internal Server Error` is returned (`{"errorCode": "PUB_SUB_ERROR", ...}`).

8.  **Return Success Response**:
    *   If the message is successfully "published" to Pub/Sub, a `202 Accepted` response is returned with the generated `messageId`:
        ```json
        {
          "messageId": "generated-uuid-12345"
        }
        ```

### Helper Functions:
*   `create_json_response(data, status_code)`: A utility to format the response dictionary that would be converted to an actual HTTP JSON response by a web framework.
*   Basic logging is implemented using the `logging` module to track key events and errors.

## 2. Stubbed Clients

*   **`CAMSClient`**:
    *   Provides a `get_agent_mapping(ai_agent_address)` method.
    *   It wraps the `getAgentMapping` function, which is imported from `services.cams.cams_api_pseudo`. A local mock of `getAgentMapping` is also included within `message_router_service.py` as a fallback if the import fails, allowing the service to be tested more independently.
*   **`PubSubPublisher`**:
    *   Provides a `publish_message(topic_name, message_data)` method.
    *   This is a conceptual placeholder for a real Google Cloud Pub/Sub publisher client.
    *   It includes a `simulate_failure` flag that can be set to `True` to test the Pub/Sub error handling path.

## 3. Assumptions

*   **CAMS Availability**: The CAMS client (`getAgentMapping`) is expected to be available and follow the interface defined in Task 02 (returning a dictionary with `status`, `inboxName`, etc., or `None`).
*   **Pub/Sub Client Availability**: A Pub/Sub client mechanism is assumed to be available for publishing messages. The stub simulates this interaction.
*   **Framework Agnostic**: The provided code is the core logic and does not include framework-specific boilerplate (like Flask or FastAPI routing setup). The `handle_message_ingestion` function would be called by the request handler of such a framework.
*   **Error Response Format**: Error responses are JSON objects with `errorCode` and `message` fields, e.g., `{"errorCode": "AGENT_NOT_FOUND", "message": "AI Agent Address '...' not found."}`.
*   **Logging**: Basic logging to stdout is used. In a production system, this would be more sophisticated.

## 4. Example Usage (`if __name__ == "__main__":`)

The `message_router_service.py` file includes an `if __name__ == "__main__":` block that demonstrates the usage of `handle_message_ingestion` with various scenarios:
*   Valid request and successful processing.
*   Agent not found in CAMS.
*   Agent found but is inactive.
*   Missing `aiAgentAddress` or `payload` in the request.
*   Invalid `payload` format (not a JSON object).
*   Simulated error during Pub/Sub publishing.
*   Valid request with minimal or no `senderMetadata`.
*   Scenario where CAMS returns an active agent but `inboxName` is missing (configuration error).

These examples use `assert` statements for basic verification of the expected outcomes (status codes and error codes).

This service fulfills the requirements for the Message Ingestion API of the Message Router Service as outlined in Task 04.
