# Windsurf Task 11: Implement Persistent Central Agent Mapping Service (CAMS)

## 1. Task Objective

This crucial task is to replace the pseudo-implementation of the Central Agent Mapping Service (CAMS) (`services/cams/cams_api_pseudo.py`) with a **production-grade persistent database backend**. This will involve setting up a real database connection, defining the schema, implementing database operations, and ensuring all CAMS interactions are robust and transactional.

This task is essential for the reliability, scalability, and persistence of our AI Agent Message Routing Component.

## 2. Context & Rationale

Currently, `cams_api_pseudo.py` simulates CAMS operations using in-memory data structures. While this was effective for initial development and testing, it is not suitable for a production environment where agent mappings must be persistent, consistent, and highly available. We need to implement CAMS using a dedicated database to ensure data integrity and scalability.

Given our `asyncio`-native architecture from Task 10, the database interactions must also be asynchronous.

## 3. Detailed Requirements

Windsurf will need to modify files within `services/cams/` and ensure compatibility with the `asyncio` framework.

### 3.1. Database Selection & Connection

* **Database:** Assume **Google Cloud SQL with PostgreSQL** as the target database.
* **Async Driver/ORM:** Use an asynchronous PostgreSQL driver/ORM for Python. **`asyncpg`** for direct driver interaction or **`SQLAlchemy` with `asyncio` support (e.g., with `asyncpg` as its dialect)** are recommended choices.
* **Connection Management:** Implement robust database connection pooling and management to ensure efficient and reliable connections.
* **Configuration:** Database connection details (host, port, user, password, database name) should be read from environment variables, consistent with our Kubernetes Secrets strategy (from Task 07).

### 3.2. CAMS Database Schema Implementation

* **Implement `agent_inboxes` table:** Create the `agent_inboxes` table within the database, based on the schema defined in `create_cams_table.sql`.
    * Ensure all fields (e.g., `aiAgentAddress`, `inboxDestinationType`, `inboxName`, `status`, `registrationTimestamp`, `lastUpdatedTimestamp`, `lastHealthCheckTimestamp`, `description`, `ownerTeam`) are correctly mapped to database column types.
    * Enforce constraints (e.g., `aiAgentAddress` as a unique primary key).

### 3.3. Implement CAMS Core API with Database Operations

* **Refactor `services/cams/cams_api_pseudo.py`:**
    * Rename `cams_api_pseudo.py` to `cams_repository.py` (or similar) to signify its role as the data access layer.
    * Replace all in-memory dictionary operations with actual **asynchronous database queries** using the chosen driver/ORM.
    * Implement the following core CRUD operations as `async def` functions:
        * `async def register_agent_mapping(...)`: Inserts a new agent mapping. Handle unique constraint violations gracefully (e.g., raising a specific error).
        * `async def get_agent_mapping(ai_agent_address: str)`: Retrieves an agent mapping by address. Return `None` or raise an exception if not found.
        * `async def update_agent_mapping_details(ai_agent_address: str, **kwargs)`: Performs partial updates based on `kwargs`. Ensure `lastUpdatedTimestamp` and `lastHealthCheckTimestamp` are updated automatically as needed.
        * `async def delete_agent_mapping(ai_agent_address: str)`: Deletes an agent mapping.
    * **Transactions:** Ensure that multi-step operations (if any develop) are wrapped in database transactions to maintain atomicity.
    * **Error Handling:** Implement robust error handling for database connection issues, query failures, and constraint violations.

### 3.4. Update Router Service CAMS Client

* The Message Router Service (and its API handlers) currently imports `cams_api_pseudo`.
* Update the import statements and ensure that the router's calls to CAMS functions are now interacting with the new `cams_repository.py` and its asynchronous methods.

### 3.5. Logging, Metrics & Error Handling

* Ensure that the logging and metrics instrumentation previously added in Task 06 continues to function correctly, capturing database operation times, success/failure rates, and errors.
* Log all database interactions (query execution, results, errors).

### 3.6. Dependencies and Project Setup

* **`requirements.txt` Update:** Add the chosen database driver/ORM (e.g., `asyncpg`, `SQLAlchemy`).
* **`Dockerfile` Update:** If the chosen database driver requires any system-level packages (e.g., `libpq-dev` for `asyncpg`), update `services/router/Dockerfile` to install them.
* **Migration Strategy (Documentation):** Briefly outline a conceptual database migration strategy (e.g., using Alembic) in the `services/cams/README.md`, even if not implemented fully in this task.

## 4. Dependencies

* **Jules Task 02 (`create_cams_table.sql`):** The defined SQL schema.
* **Jules Task 05 & Windsurf Task 08:** The CAMS API interface functions (register, get, update, delete, health check updates) that now need to interact with a real DB.
* **Windsurf Task 10:** The `asyncio`-native refactoring, which ensures CAMS can use async database drivers.
* **Windsurf Task 07:** Dockerfile for system package updates if needed.

## 5. Expected Output from Windsurf

Upon completion, Windsurf should provide:

* **Modified `services/cams/cams_repository.py`**: The refactored CAMS implementation with real database interactions.
* **Updated `services/router/Dockerfile`**: If new system packages are required for the database driver.
* **Updated `requirements.txt`**: With new Python database dependencies.
* **Updated `services/cams/README.md`**: Detailing the database choice, connection configuration, data access layer implementation, and conceptual migration strategy.
* **Confirmation:** That all existing CAMS-related functionalities (agent registration, lookups, status updates via health checks) continue to work correctly with the new persistent backend.

## 6. Output Location

All modified files will remain in their existing locations (`services/cams/`, `services/router/`), and `requirements.txt` will be updated (assume `services/router/requirements.txt`).

---

This is a very impactful task, Windsurf. It moves our CAMS from a pseudo-service to a production-ready component. Let me know if you have any questions or require further clarification!