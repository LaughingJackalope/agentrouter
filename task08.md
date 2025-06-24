# Windsurf Task 08: Develop Agent Health Check Reporting Mechanism

## 1. Task Objective

This task is to design and implement a basic health check reporting mechanism for AI Agents. This mechanism will allow AI Agents to report their health status to the Message Routing Component, which can then be used to update their status in the Central Agent Mapping Service (CAMS) and inform routing decisions.

This aligns with **Phase 2: Management & Operational Readiness**, specifically **"Develop Agent Health Check Reporting Mechanism"** in our Pragmatic Development Roadmap.

## 2. Context & Rationale

Currently, an AI Agent's `status` in CAMS (ACTIVE/INACTIVE) is updated manually via the Agent Management API (Task 05). For robust routing and to prevent sending messages to unhealthy agents, we need an automated way for agents to report their operational status.

This health check mechanism will allow:
* The Message Router to query CAMS for an agent's real-time health status before routing.
* Automated deactivation of unhealthy agents in CAMS.
* Better insights into overall agent ecosystem health.

## 3. Detailed Requirements

Windsurf should implement a conceptual API endpoint for agents to report their health, and update the CAMS interaction logic accordingly.

### 3.1. Agent Health Check API Endpoint

Define a new API endpoint that AI Agents can call to report their health.

* **Endpoint:** `POST /v1/agent-health-check` (or `PUT` if idempotent updates are preferred)
* **Purpose:** Allow AI Agents to self-report their health status.
* **Request Payload (JSON):**
    ```json
    {
      "aiAgentAddress": "string",             // REQUIRED. The address of the reporting agent.
      "status": "string",                     // REQUIRED. The agent's self-reported health status.
                                              //   For MVP, assume simple: "HEALTHY", "UNHEALTHY".
      "details": "string"                     // OPTIONAL. Additional human-readable details (e.g., error messages).
    }
    ```
* **Successful Response:**
    * **HTTP Status:** `200 OK` or `204 No Content`
    * **Response Body:** Minimal or empty.
* **Error Handling:**
    * `400 Bad Request` for invalid input.
    * `404 Not Found` if `aiAgentAddress` is not registered in CAMS.
    * `500 Internal Server Error` for internal processing issues.

### 3.2. Integration with CAMS

The `POST /v1/agent-health-check` endpoint's handler should:

1.  **Validate Input:** Ensure `aiAgentAddress` and `status` are present and valid.
2.  **CAMS Lookup:**
    * Call `cams_client.getAgentMapping(aiAgentAddress)` to retrieve the agent's current mapping.
    * If the agent is not found, return `404 Not Found`.
3.  **Update Agent Status in CAMS:**
    * Call `cams_client.updateAgentMappingDetails(aiAgentAddress, status=new_status, lastHealthCheckTimestamp=current_timestamp_utc)`.
    * Map the incoming `status` ("HEALTHY" / "UNHEALTHY") to `ACTIVE` / `INACTIVE` for the `status` field in the `agent_inboxes` table if the CAMS `status` field is used for this purpose. *Clarification: The CAMS `status` field (`ACTIVE`/`INACTIVE`) is for router-level routing decisions. The health check `status` (`HEALTHY`/`UNHEALTHY`) influences this. If a `HEALTHY` report comes in, set CAMS `status` to `ACTIVE`. If `UNHEALTHY`, set to `INACTIVE`. This requires updating the `updateAgentMappingDetails` function in CAMS (Task 05's update).*
    * Crucially, update the `lastHealthCheckTimestamp` in CAMS to the current UTC timestamp for this agent.
4.  **Logging & Metrics:**
    * Log all health check reports received (INFO).
    * Log CAMS update success/failure (INFO/ERROR).
    * Increment metrics for health check reports received (total, by agent, by reported status).
    * Increment metrics for CAMS status updates due to health checks.

### 3.3. CAMS Schema Enhancement (Minor)

While `lastHealthCheckTimestamp` is already in the `agent_inboxes` schema, ensure its usage is aligned with this task. The `status` field in CAMS will be directly driven by these health checks.

### 3.4. Technology Stack / Language

* Implementation should be in **Python**.
* Assume the use of conceptual `cams_client` and `metrics_collector` as integrated in Task 06.

## 4. Dependencies

* **Jules Task 02/05 Output:** CAMS Core API and Agent Management APIs, especially the `updateAgentMappingDetails` function.
* **Windsurf Task 06 Output:** Logging and Metrics instrumentation.

## 5. Expected Output from Windsurf

Upon completion, Windsurf should provide:

* **`services/router/agent_health_check_api.py`**: A new Python file containing the handler logic for the `POST /v1/agent-health-check` endpoint.
* **Updates to existing files:** Minor modifications to `services/cams/cams_api_pseudo.py` if the mapping from agent health status (`HEALTHY`/`UNHEALTHY`) to CAMS `status` (`ACTIVE`/`INACTIVE`) requires it (e.g., adding logic within `updateAgentMappingDetails` or a new CAMS function to manage agent operational status directly from health checks).
* **Updates to `services/router/README.md` or a new `services/router/health_check_guide.md`**: Documenting the new API endpoint, its payload, and how health checks influence CAMS status.
* **Updates to `docs/observability/observability_guide.md`**: Documenting any new metrics related to health checks.

## 6. Output Location

* New API handler: `services/router/agent_health_check_api.py`
* Updated CAMS pseudo-code: `services/cams/cams_api_pseudo.py`
* Documentation: Update existing `README.md` files or create new ones as appropriate in `services/router/` and `docs/observability/`.

---

This task will give us automated insight into our AI Agents' operational status. Let me know if this is clear for Windsurf, Pilot!