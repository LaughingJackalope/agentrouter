# Jules Task 02: Implement Central Agent Mapping Service (CAMS) - Core API & Persistence

## 1. Task Objective

This task is to define the database schema for the Central Agent Mapping Service (CAMS) and to implement its core CRUD (Create, Read, Update, Delete) operations. CAMS will serve as the authoritative source for mapping `AI Agent Addresses` to their respective inbox destinations (e.g., Pub/Sub topics) and managing their active status.

This aligns with **Phase 1: Core Routing MVP**, specifically **"Implement Central Agent Mapping Service (CAMS) - Core API & Persistence"** in our Pragmatic Development Roadmap.

## 2. Context & Rationale

The Central Agent Mapping Service (CAMS) is a critical component for the Message Router. Before routing any message, the router must query CAMS to:
* Resolve the `aiAgentAddress` to its `inboxName` (Pub/Sub topic).
* Check the `status` of the target AI Agent (e.g., `ACTIVE` or `INACTIVE`).

CAMS must be highly available and performant for read operations, as every message ingestion will trigger a lookup.

## 3. Detailed Requirements

### 3.1. Database Technology

* **Primary Database:** **Google Cloud SQL (PostgreSQL or MySQL)** is the chosen database technology for the MVP. Jules should provide SQL DDL that is compatible with either, preferably PostgreSQL as it's a common choice, but should explicitly state which one is used.
* **Scalability Note:** While Cloud Spanner is noted for extreme scale in the overall design, for this MVP task, the focus is on Cloud SQL.

### 3.2. CAMS Database Schema

Define a single table, `agent_inboxes`, with the following columns:

* **`aiAgentAddress` (VARCHAR(255), Primary Key, NOT NULL):**
    * Purpose: The unique identifier for an AI Agent.
    * Indexing: This will be the primary key, automatically indexed for fast lookups.
* **`inboxDestinationType` (VARCHAR(50), NOT NULL):**
    * Purpose: Specifies the type of destination. For this MVP, the value will always be `'GCP_PUBSUB_TOPIC'`.
    * Example: `"GCP_PUBSUB_TOPIC"`
* **`inboxName` (VARCHAR(255), NOT NULL):**
    * Purpose: The actual name of the Pub/Sub topic associated with the `aiAgentAddress`.
    * Example: `"projects/your-gcp-project/topics/agent-sales-inbox"`
* **`status` (VARCHAR(20), NOT NULL, DEFAULT 'ACTIVE'):**
    * Purpose: Indicates the operational status of the AI Agent. The Message Router will only route messages to `ACTIVE` agents.
    * Allowed Values: `'ACTIVE'`, `'INACTIVE'`
* **`lastHealthCheckTimestamp` (TIMESTAMP WITH TIME ZONE, OPTIONAL):**
    * Purpose: Records the last time the AI Agent reported a successful heartbeat. Will be updated by an external health check mechanism.
    * Format: UTC timestamp (ISO 8601).
* **`registrationTimestamp` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT CURRENT_TIMESTAMP):**
    * Purpose: Records when the agent mapping was first registered in CAMS.
    * Format: UTC timestamp (ISO 8601).
* **`lastUpdatedTimestamp` (TIMESTAMP WITH TIME ZONE, NOT NULL, DEFAULT CURRENT_TIMESTAMP):**
    * Purpose: Records the last time any information for this agent mapping was updated. Should update on every modify operation.
    * Format: UTC timestamp (ISO 8601).
* **`updatedBy` (VARCHAR(255), OPTIONAL):**
    * Purpose: Records the entity (user or service) that last updated the record.
* **`description` (TEXT, OPTIONAL):**
    * Purpose: A human-readable description of the agent or its purpose.
* **`ownerTeam` (VARCHAR(255), OPTIONAL):**
    * Purpose: Identifies the team responsible for managing this AI Agent.

**Important Note on Audit Trail:** As discussed in design, the `auditTrail` is a logical concept and will be handled via external logging to Google Cloud Logging/BigQuery, not as an in-database JSONB field for this `agent_inboxes` table.

### 3.3. Core API / Operations (Conceptual - Python Pseudo-code)

Jules should provide Python pseudo-code (or a basic Python class/functions) for the following core CAMS operations. These operations should interact with a conceptual database layer (e.g., `db_client.execute_query`).

* **`registerAgentMapping(aiAgentAddress, inboxDestinationType, inboxName, description=None, ownerTeam=None)`:**
    * Purpose: Creates a new agent mapping record. `status` should default to `ACTIVE`.
    * Inputs: All required schema fields.
    * Output: Confirmation of creation (e.g., `True`/`False` or the created record data).
    * Considerations: Handle duplicate `aiAgentAddress` (e.g., raise an error).

* **`getAgentMapping(aiAgentAddress)`:**
    * Purpose: Retrieves a single agent mapping record by its `aiAgentAddress`.
    * Inputs: `aiAgentAddress` (string).
    * Output: The full agent mapping record (dictionary/object) or `None` if not found.

* **`updateAgentStatus(aiAgentAddress, newStatus)`:**
    * Purpose: Updates only the `status` field for a given agent.
    * Inputs: `aiAgentAddress` (string), `newStatus` (string, must be 'ACTIVE' or 'INACTIVE').
    * Output: Boolean indicating success.
    * Considerations: Update `lastUpdatedTimestamp`.

* **`updateAgentInbox(aiAgentAddress, newInboxDestinationType, newInboxName)`:**
    * Purpose: Updates the inbox destination details for an agent.
    * Inputs: `aiAgentAddress` (string), `newInboxDestinationType` (string), `newInboxName` (string).
    * Output: Boolean indicating success.
    * Considerations: Update `lastUpdatedTimestamp`.

* **`deleteAgentMapping(aiAgentAddress)`:**
    * Purpose: Removes an agent mapping record.
    * Inputs: `aiAgentAddress` (string).
    * Output: Boolean indicating success.

### 3.4. Assumptions

* Jules should assume a generic Python database client (`db_client`) for the pseudo-code, as the actual database connection and ORM setup will be handled in later implementation steps.
* Focus on the logical operations and their inputs/outputs based on the schema.

## 4. Expected Output from Jules

Upon completion, Jules should provide:

* A SQL DDL file (e.g., `create_cams_table.sql`) containing the `CREATE TABLE` statement for the `agent_inboxes` table, compatible with PostgreSQL (or MySQL, with explicit notation).
* A Python file (e.g., `cams_api_pseudo.py`) containing the pseudo-code implementations for the `registerAgentMapping`, `getAgentMapping`, `updateAgentStatus`, `updateAgentInbox`, and `deleteAgentMapping` functions.
* A `README.md` file within the output directory explaining the CAMS schema and the provided pseudo-code, including any assumptions made.

## 5. Output Location

Please place all output files for this task in a new directory named `services/cams/` within the repository root.

