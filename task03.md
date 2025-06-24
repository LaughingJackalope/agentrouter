# Jules Task 03: Set Up Google Pub/Sub Topics & Subscriptions for AI Agent Inboxes

## 1. Task Objective

This task is to define the strategy and provide the necessary scripts/guidance for dynamically setting up Google Pub/Sub topics and associated subscriptions, which will serve as the "inboxes" for individual AI Agents. This includes establishing naming conventions and configuring Dead Letter Queues (DLQs).

This aligns with **Phase 1: Core Routing MVP**, specifically **"Set Up Pub/Sub Topics & Subscriptions for Agent Inboxes"** in our Pragmatic Development Roadmap.

## 2. Context & Rationale

Google Pub/Sub is the core asynchronous message transport layer for the AI Agent Message Routing Component. Each AI Agent will have a dedicated Pub/Sub Topic that acts as its "inbox," and a corresponding subscription from which it consumes messages. This design ensures:
* **Scalability:** Pub/Sub handles message volumes automatically.
* **Decoupling:** The router doesn't need direct knowledge of agent consumption logic.
* **Reliability:** Pub/Sub's at-least-once delivery and DLQ capabilities ensure messages are not lost.

## 3. Detailed Requirements

### 3.1. Dynamic Provisioning Strategy

The creation of Pub/Sub topics and subscriptions will be **dynamic**, meaning they will be provisioned as new AI Agents are registered in the Central Agent Mapping Service (CAMS). This task should define the pattern and methods for this provisioning, rather than creating static instances.

### 3.2. Naming Conventions

Consistent naming is critical for manageability and auditability.

* **Pub/Sub Topic Naming:**
    * **Format:** `agent-inbox-<aiAgentAddress-sanitized-hash>`
    * **Details:** The `aiAgentAddress` (e.g., `agent-sales@yourorg.com`) will be used to derive a unique, URL-safe name. A simple approach is to convert the `aiAgentAddress` to lowercase, replace non-alphanumeric characters with hyphens, and then take a **SHA-256 hash** of the result to ensure a consistent, fixed-length, and unique identifier suitable for topic names (which have length limits and character restrictions). This also helps obscure the full email address in the topic name for security reasons.
    * **Example (Conceptual):** If `aiAgentAddress` is `agent-sales@yourorg.com`, the topic name might be `agent-inbox-1c3a2b...` (where `1c3a2b...` is a hash).
    * **Constraint:** Pub/Sub topic names must start with a letter, and contain only letters, numbers, dashes (`-`), and underscores (`_`). Max length 255 characters. The hashing helps conform to this.

* **Pub/Sub Subscription Naming:**
    * **Format:** `agent-sub-<aiAgentAddress-sanitized-hash>-<consumer-group-id>`
    * **Details:** The subscription name should indicate that it's for an agent's inbox and link to the same hash used for the topic. A `<consumer-group-id>` can be added to allow for multiple, independent consumers of the same topic if needed in the future (for MVP, a default like `main-consumer` is fine).
    * **Example:** `agent-sub-1c3a2b...-main-consumer`

### 3.3. Subscription Configuration

Each subscription must be configured as follows:

* **Type:** **Pull Subscription**. AI Agents will "pull" messages from their subscription.
* **Acknowledgement Deadline:** Default (e.g., 10 seconds).
* **Message Retention Duration:** Default (e.g., 7 days).
* **Enable Message Ordering:** No, not required for MVP.
* **Enable BigQuery Export:** No.

### 3.4. Dead Letter Queue (DLQ) Configuration

Each Pub/Sub subscription **must** be configured with a native Dead Letter Queue (DLQ) topic.

* **DLQ Topic Naming:**
    * **Format:** `dlq-agent-inbox-<aiAgentAddress-sanitized-hash>`
    * **Details:** Directly linked to the main agent inbox topic.
    * **Example:** `dlq-agent-inbox-1c3a2b...`

* **DLQ Redelivery Policy:**
    * **Maximum Delivery Attempts:** Set to `5`. Messages that fail to be acknowledged after 5 attempts by the subscriber will be moved to the DLQ.

### 3.5. IAM Permissions (Conceptual)

Briefly outline the required IAM permissions for:
* **Message Router Service Account:** Needs `pubsub.publisher` role on the agent inbox topics.
* **AI Agent Consumer Service Account:** Needs `pubsub.subscriber` role on its specific agent inbox subscription.
* **Provisioning Service Account:** Needs `pubsub.editor` or custom roles to create/manage topics and subscriptions.

### 3.6. GCP Project Context

Assume all resources (topics, subscriptions, DLQs) are created within a specified Google Cloud Project ID. Let's use `your-gcp-project-id` as a placeholder.

## 4. Expected Output from Jules

Upon completion, Jules should provide:

* A **Python script** (e.g., `pubsub_provisioning.py`) that includes functions for:
    * Generating the hashed topic/subscription/DLQ names from an `aiAgentAddress`.
    * Programmatically creating a Pub/Sub topic.
    * Programmatically creating a Pub/Sub pull subscription, linked to the topic and configured with a DLQ.
    * An example of how these functions would be used when an agent is registered (e.g., `provision_agent_inbox(aiAgentAddress, gcp_project_id)`).
* A **`README.md`** file within the output directory explaining:
    * The naming conventions in detail.
    * The Pub/Sub and DLQ configuration parameters.
    * The conceptual IAM roles needed.
    * Examples of using the Python script or equivalent `gcloud` commands for manual verification.

## 5. Output Location

Please place all output files for this task in a new directory named `gcp/pubsub_setup/` within the repository root.

---

Let me know if this task is clear, Pilot! This will set us up nicely for the actual router implementation.
