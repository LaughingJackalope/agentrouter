# Windsurf Task 10: Refactor to Async-Native Architecture (ASGI/Asyncio)

## 1. Task Objective

This crucial task is to refactor the entire Message Routing Component codebase to be fully **async-native**, adhering to the `asyncio` concurrency model and utilizing an ASGI-compatible framework. This will involve transforming all I/O paths to be explicitly `awaitable`, replacing blocking calls, and configuring the services for ASGI deployment.

This refactoring is critical for ensuring the system's performance, scalability under load, and future-proofing against legacy concurrency models.

## 2. Context & Rationale

Our analysis indicates that while the current pseudo-code is functional, its underlying concurrency model (or potential implicit blocking I/O) is not suited for the high-throughput, low-latency requirements of our message router in a 2025 context. We must transition from any blocking I/O patterns (like those implicitly using `gevent` or synchronous libraries) to `asyncio` to leverage non-blocking I/O efficiently. This involves adopting an ASGI framework and `async` database drivers.

## 3. Detailed Requirements (Transition Playbook: `gevent` → `asyncio`)

Windsurf will need to modify existing Python files (`services/router/*.py`, `services/cams/cams_api_pseudo.py`), the `Dockerfile`, and Kubernetes manifests.

### 3.1. Adopt an ASGI-First Framework

* **Replace current API framework:** Transition the Message Router Service from its current conceptual framework (likely Flask-like, which is WSGI-based) to an **ASGI-first framework**. **FastAPI** is the recommended choice due to its performance, built-in validation, and strong `asyncio` support.
* **Refactor API Endpoints:** All existing API endpoints (`POST /v1/messages`, `POST /v1/agent-inboxes`, `GET /v1/agent-inboxes/{aiAgentAddress}`, `PUT /v1/agent-inboxes/{aiAgentAddress}`, `DELETE /v1/agent-inboxes/{aiAgentAddress}`, `POST /v1/agent-health-check`) must be implemented using `async def` and `await` where appropriate within the FastAPI handlers.

### 3.2. Replace Blocking I/O Libraries with Async Equivalents

* **CAMS Database Interactions:**
    * Since `cams_api_pseudo.py` is currently pseudo-code, assume its underlying database interactions would be blocking (e.g., with `psycopg2` or `mysql-connector`).
    * **Refactor `cams_api_pseudo.py`:** Update the methods within `cams_api_pseudo.py` (e.g., `registerAgentMapping`, `getAgentMapping`, `updateAgentMappingDetails`, `deleteAgentMapping`) to conceptually use **async database drivers**. If PostgreSQL is the target for Cloud SQL, suggest `asyncpg`. If MySQL, suggest `aiomysql`. The actual connection pooling/client setup can remain conceptual, but the *method signatures and internal calls* should be `async def`/`await` compatible.
* **External HTTP Calls (if any):** If the Router or CAMS made any external HTTP calls using `requests`, replace them with `httpx` (its async client).
* **File I/O (if any):** Ensure any file I/O operations are handled asynchronously where possible, using `aiofiles` or `asyncio.to_thread` for truly blocking OS calls.

### 3.3. Run under Uvicorn

* **Dockerfile Update:** Modify `services/router/Dockerfile` to use **`uvicorn`** as the ASGI server instead of `gunicorn` (or a default Flask server).
    * The `CMD` or `ENTRYPOINT` should reflect running FastAPI with `uvicorn` (e.g., `uvicorn main:app --host 0.0.0.0 --port 8080 --loop uvloop`).
* **Kubernetes Manifests Update:** Update `router-deployment.yaml` to reflect the `uvicorn` command for running the container.

### 3.4. Ensure All I/O Paths are Explicitly Awaitable

* Conduct an audit of the codebase to identify any remaining blocking I/O calls.
* Ensure that all functions that perform I/O (database, network, disk) are marked `async def` and their calls are `await`ed.
* **Ban Monkey-Patching:** Explicitly ensure no `monkey-patching` libraries (like `gevent.monkey`) are used or introduced.

### 3.5. Update Dependencies

* **`requirements.txt`:** Update `requirements.txt` to include `fastapi`, `uvicorn[standard]` (or `uvicorn[standard,uvloop]`), `httpx`, and the chosen async database driver (e.g., `asyncpg`).

### 3.6. Logging & Metrics Integration

* Ensure that the logging and metrics instrumentation implemented in Task 06 continues to function correctly within the `asyncio` context. FastAPI's logging integration is generally good.

## 4. Dependencies

* **All previous tasks:** The full codebase as it stands after Task 08, including API implementations, CAMS pseudo-code, Dockerfile, Kubernetes manifests, and observability setup.

## 5. Expected Output from Windsurf

Upon completion, Windsurf should provide:

* **Modified Python Files:** All files in `services/router/` and `services/cams/` will be refactored to use `async def`/`await` and async libraries.
* **Updated `services/router/Dockerfile`**: Configured to run the FastAPI application with `uvicorn`.
* **Updated `deployment/kubernetes/router-deployment.yaml`**: Reflecting the `uvicorn` command.
* **Updated `requirements.txt`**: Listing all new and modified dependencies.
* **Updated `README.md` files:**
    * `services/router/README.md`: Documenting the transition to FastAPI/ASGI, how to run locally with Uvicorn.
    * `services/cams/README.md`: Documenting the conceptual async database driver usage.
    * `docs/observability/observability_guide.md`: Confirming compatibility with the new async framework.

## 6. Output Location

All modified files will remain in their existing locations, and `requirements.txt` will be updated in its existing location (assume `services/router/requirements.txt`).
