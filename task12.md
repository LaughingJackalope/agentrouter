

# Windsurf Task 12: Integrate Router Service with Persistent CAMS Backend

## 1. Task Objective

This task is to update the Message Router Service to replace its current interaction with the in-memory CAMS (`cams_api_pseudo.py`) with the newly implemented **persistent and asynchronous CAMS repository (`cams_repository.py`)**. This involves updating import paths and ensuring all CAMS interactions within the router (including Message Ingestion, Agent Management APIs, and Agent Health Checks) correctly utilize the new database-backed CAMS.

## 2. Context & Rationale

We have successfully developed the persistent CAMS backend in Task 11. The Router Service (implemented across various files in `services/router/`) currently uses the placeholder CAMS implementation. For the Message Routing Component to function with persistent data and leverage the scalability benefits of the new CAMS, the router must be updated to interact with the real CAMS repository.

## 3. Detailed Requirements

Windsurf will need to modify files within `services/router/` to update CAMS imports and ensure all existing CAMS-related functionalities work seamlessly with the new backend.

### 3.1. Update CAMS Import Paths

* Identify all Python files within `services/router/` that import or directly reference `services/cams/cams_api_pseudo.py` (or any related CAMS mock objects).
* Change these import statements to correctly import and instantiate the new `services/cams/cams_repository.py` (or whatever the final name is after the refactor).

### 3.2. Ensure Asynchronous CAMS Interactions

* Verify that all calls from the Router Service to CAMS methods (e.g., `get_agent_mapping`, `register_agent_mapping`, `update_agent_mapping_details`, `delete_agent_mapping`) are now correctly `await`ed, given that the `cams_repository.py` methods are `async def`. This should be mostly handled by the work in Task 10, but a final check is crucial.
* Ensure the CAMS client instance is properly initialized, potentially passing database connection details (derived from environment variables configured in the Router's environment, as discussed in Task 07).

### 3.3. Verify End-to-End Functionality

* **Message Ingestion API (`POST /v1/messages`):** Confirm that messages are successfully routed after the agent's mapping is retrieved from the *persistent* CAMS.
* **Agent Management APIs (`/v1/agent-inboxes` CRUD):** Test that creating, retrieving, updating, and deleting agent mappings via these APIs now correctly affects the *persistent* database.
* **Agent Health Check API (`POST /v1/agent-health-check`):** Verify that health check reports correctly update the agent's status and `lastHealthCheckTimestamp` in the *persistent* database.

### 3.4. Logging & Metrics

* Ensure that existing logging and metrics (from Task 06) continue to capture CAMS interaction details (latency, success/failure) correctly, now reflecting the real database calls.

### 3.5. Documentation Updates

* Update `services/router/README.md` if there are any new setup steps or configurations related to the CAMS integration.
* Ensure that any example usage or testing instructions are still valid.

## 4. Dependencies

* **Windsurf Task 10:** Async-Native Refactoring (ensures Router is ready for `async` CAMS calls).
* **Windsurf Task 11:** Persistent CAMS Backend Implementation (`cams_repository.py` is now available).
* **Jules Task 05 & Windsurf Task 08:** The existing API endpoints in the Router that interact with CAMS.

## 5. Expected Output from Windsurf

Upon completion, Windsurf should provide:

* **Modified Python Files:** Updated files within `services/router/` (e.g., `message_router_service.py`, `agent_management_api.py`, `agent_health_check_api.py`) where CAMS is used.
* **Confirmation:** A detailed summary confirming that all CAMS interactions within the Router Service are now fully integrated with the persistent CAMS backend and that all related API functionalities (message routing, agent management, health checks) are working correctly end-to-end with persistent data.
* **Updates to `README.md`:** Any necessary updates to reflect the integration.

## 6. Output Location

All modified files will remain in their existing locations.

---