# Windsurf Task 06: Implement Comprehensive Logging & Metrics

## 1. Task Objective

This task is to implement comprehensive logging and metrics instrumentation across the core components of the AI Agent Message Routing System, specifically within the Router Service (`services/router/`) and the Central Agent Mapping Service (CAMS) pseudo-code (`services/cams/`). The goal is to provide deep operational visibility for monitoring, troubleshooting, and performance analysis.

This aligns with **Phase 2: Management & Operational Readiness**, and directly addresses the need for **"Develop Comprehensive Logging & Metrics"** in our Pragmatic Development Roadmap.

## 2. Context & Rationale

As we move towards operationalizing the Message Routing Component, robust logging and metrics are paramount. They enable us to:
* **Troubleshoot Issues:** Quickly identify and diagnose problems in the message flow or CAMS interactions.
* **Monitor Performance:** Track latency, throughput, and error rates to ensure we meet our non-functional requirements.
* **Auditability:** Provide a clear trail of message processing and agent management actions.
* **Proactive Alerting:** Set up alerts based on deviations in metrics or critical log events.

## 3. Detailed Requirements

Windsurf will need to modify existing Python files within `services/router/` and `services/cams/`.

### 3.1. Logging Implementation

* **Standard Python Logging:** Utilize Python's built-in `logging` module.
* **Structured Logging (JSON):** Configure log formatters to output logs in a structured JSON format suitable for ingestion by Google Cloud Logging. This allows for easier parsing and querying.
* **Key Log Events & Data Points:**
    * **Message Ingestion API (`POST /v1/messages` - `services/router/message_router_service.py`):**
        * **On Request Receive (INFO):** Log incoming request details (e.g., `aiAgentAddress`, `correlationId` if present, `senderId` if present).
        * **On CAMS Lookup (INFO/DEBUG):** Log the result of the CAMS lookup (agent found/not found, status).
        * **On Pub/Sub Publish (INFO):** Log successful publication, including the generated `messageId`, `aiAgentAddress`, and the target `inboxName`.
        * **On Success (INFO):** Log the successful processing and `202 Accepted` response.
        * **On Validation Error (WARNING/ERROR):** Log details of `400 Bad Request` responses (e.g., missing fields).
        * **On CAMS/Routing Error (WARNING/ERROR):** Log details of `404 Not Found` responses (agent not found/inactive).
        * **On Internal Server Error (ERROR):** Log full details of `500 Internal Server Error` (e.g., Pub/Sub publish failure, unexpected exceptions).
        * **Traceability:** Ensure `messageId`, `aiAgentAddress`, `correlationId`, `senderId` (if applicable) are consistently included in log entries related to message processing for end-to-end traceability.
    * **CAMS Core API (`services/cams/cams_api_pseudo.py`):**
        * **On CRUD Operation (INFO):** Log successful `registerAgentMapping`, `getAgentMapping`, `updateAgentMappingDetails`, `deleteAgentMapping` calls (e.g., "Agent registered: [address]").
        * **On CAMS Error (ERROR):** Log database interaction failures, duplicate key errors, or other internal CAMS errors.
        * **Traceability:** If CAMS operations are part of a larger flow, include relevant IDs (e.g., from an API request context) in CAMS logs if available.
* **Log Levels:** Use appropriate log levels (`INFO`, `WARNING`, `ERROR`, `DEBUG`) to control verbosity.

### 3.2. Metrics Instrumentation

* **Metrics Library:** Integrate a conceptual metrics client (e.g., an OpenTelemetry or Prometheus client if using a Python framework that supports it, or simple counter/gauge increments for pseudo-code). The focus is on *what* metrics to expose and *where* to increment them.
* **Key Metrics to Expose:**
    * **`mrc_requests_total` (Counter):** Total number of incoming API requests to `POST /v1/messages`.
        * Labels: `endpoint`, `method`, `status_code` (e.g., `202`, `400`, `404`, `500`).
    * **`mrc_request_latency_seconds` (Histogram/Summary):** Latency of the `POST /v1/messages` endpoint.
        * Labels: `endpoint`, `method`.
    * **`mrc_pubsub_published_messages_total` (Counter):** Total messages successfully published to Pub/Sub.
        * Labels: `ai_agent_address`, `topic_name`.
    * **`mrc_pubsub_publish_failures_total` (Counter):** Total messages that failed to publish to Pub/Sub.
        * Labels: `ai_agent_address`, `topic_name`, `error_type`.
    * **`cams_lookup_total` (Counter):** Total CAMS lookup operations.
        * Labels: `status` (e.g., `found`, `not_found`, `inactive`).
    * **`cams_lookup_latency_seconds` (Histogram/Summary):** Latency of CAMS lookup operations.
    * **`cams_write_operations_total` (Counter):** Total CAMS write operations (register, update, delete).
        * Labels: `operation_type` (e.g., `register`, `update`, `delete`), `status` (e.g., `success`, `failure`).
* **Granularity:** Where possible, include labels that allow for breaking down metrics by `aiAgentAddress` (or a hashed/generalized version for cardinality control), `status`, or `error_type`.

## 4. Code Modification Strategy

Windsurf should identify the relevant points within the existing Python files (`message_router_service.py`, `agent_management_api.py`, `cams_api_pseudo.py`) to insert logging statements and metric increments.

* **No new major features:** This task is purely about adding observability to *existing* functionality.
* **Minimal impact on core logic:** The additions should not alter the primary business logic flow.

## 5. Expected Output from Windsurf

Upon completion, Windsurf should provide:

* **