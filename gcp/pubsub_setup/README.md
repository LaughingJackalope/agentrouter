# Google Cloud Pub/Sub Setup for AI Agent Inboxes

This directory contains scripts and documentation for provisioning Google Cloud Pub/Sub topics and subscriptions that serve as inboxes for individual AI Agents. This setup is crucial for the AI Agent Message Routing Component.

## Table of Contents
1. [Overview](#overview)
2. [Naming Conventions](#naming-conventions)
    - [Agent Address Sanitization and Hashing](#agent-address-sanitization-and-hashing)
    - [Pub/Sub Topic Naming](#pubsub-topic-naming)
    - [Pub/Sub Subscription Naming](#pubsub-subscription-naming)
    - [DLQ Topic Naming](#dlq-topic-naming)
3. [Pub/Sub Configuration](#pubsub-configuration)
    - [Main Agent Topic](#main-agent-topic)
    - [DLQ Topic](#dlq-topic)
    - [Subscription](#subscription)
4. [IAM Permissions (Conceptual)](#iam-permissions-conceptual)
5. [Provisioning Script (`pubsub_provisioning.py`)](#provisioning-script-pubsub_provisioningpy)
    - [Prerequisites](#prerequisites)
    - [Usage](#usage)
    - [Example](#example)
6. [Manual Verification/Creation with `gcloud`](#manual-verificationcreation-with-gcloud)
    - [Setting Project ID](#setting-project-id)
    - [Creating Topics](#creating-topics)
    - [Creating Subscription with DLQ](#creating-subscription-with-dlq)
    - [Verifying Resources](#verifying-resources)

## 1. Overview

Each AI Agent requires a dedicated Pub/Sub topic (its "inbox") and a corresponding subscription for message consumption. To handle message processing failures, each subscription is configured with a Dead Letter Queue (DLQ), which is itself another Pub/Sub topic.

The provisioning of these resources is intended to be dynamic, typically triggered when a new AI Agent is registered with a central service. The provided Python script (`pubsub_provisioning.py`) automates this setup.

## 2. Naming Conventions

Consistent naming is vital for manageability. All names are derived from the AI Agent's address (e.g., `agent-sales@yourorg.com`).

### Agent Address Sanitization and Hashing

To ensure names are unique, URL-safe, and conform to Pub/Sub naming restrictions (length, characters), the `aiAgentAddress` undergoes a sanitization and hashing process:
1.  **Lowercase Conversion:** The address is converted to lowercase (e.g., `agent-sales@yourorg.com` -> `agent-sales@yourorg.com`).
2.  **Sanitization:** Non-alphanumeric characters (any character not `a-z`, `0-9`) are replaced with hyphens (`-`). Multiple consecutive hyphens are collapsed into a single hyphen. Leading/trailing hyphens are removed.
    *   Example: `agent-sales.support@example-org.com` becomes `agent-sales-support-example-org-com`.
3.  **Hashing:** The sanitized string is then hashed using **SHA-256**. The hexadecimal representation of this hash is used in resource names.
    *   Example Hash (truncated for brevity): `1c3a2b4f...`

Let `<hashed-address>` represent the result of this process.

### Pub/Sub Topic Naming (Agent Inbox)
*   **Format:** `agent-inbox-<hashed-address>`
*   **Example:** `agent-inbox-1c3a2b4f...`
*   **Constraints:** Pub/Sub topic names must start with a letter and contain only letters, numbers, dashes (`-`), periods (`.`), underscores (`_`), tildes (`~`), plus signs (`+`), and percent signs (`%`). Max length 255 characters. The prefix `agent-inbox-` ensures it starts with a letter, and the SHA-256 hash (64 hex characters) fits well within length limits.

### Pub/Sub Subscription Naming
*   **Format:** `agent-sub-<hashed-address>-<consumer-group-id>`
*   **Default `consumer-group-id`:** `main-consumer`
*   **Example:** `agent-sub-1c3a2b4f...-main-consumer`
*   **Constraints:** Similar to topic names.

### DLQ Topic Naming
*   **Format:** `dlq-agent-inbox-<hashed-address>`
*   **Example:** `dlq-agent-inbox-1c3a2b4f...`
*   **Constraints:** Same as other topic names.

## 3. Pub/Sub Configuration

### Main Agent Topic
*   No special configuration beyond its name. Standard Pub/Sub topic defaults apply.

### DLQ Topic
*   No special configuration beyond its name. Standard Pub/Sub topic defaults apply. It serves as the destination for undeliverable messages.

### Subscription
*   **Type:** Pull Subscription.
*   **Acknowledgement Deadline:** `10 seconds`. This is the time the subscriber has to acknowledge a message before Pub/Sub redelivers it.
*   **Message Retention Duration:** `7 days`. How long messages are retained, even if acknowledged (though `retain_acked_messages` is typically false for pull subscriptions).
*   **Enable Message Ordering:** No (not configured, defaults to false).
*   **Dead Letter Queue (DLQ) Configuration:**
    *   **Dead Letter Topic:** The corresponding `dlq-agent-inbox-<hashed-address>` topic.
    *   **Maximum Delivery Attempts:** `5`. After 5 failed delivery attempts (i.e., message not acknowledged within the deadline), the message is sent to the DLQ topic.

## 4. IAM Permissions (Conceptual)

The following IAM roles are conceptually required for different components interacting with these Pub/Sub resources. Apply these to the appropriate service accounts.

*   **Message Router Service Account** (The component sending messages *to* agent inboxes):
    *   Role: `roles/pubsub.publisher`
    *   Resource: On each `agent-inbox-<hashed-address>` topic it needs to publish to, or on the project if it needs to publish to any/all such topics.

*   **AI Agent Consumer Service Account** (The AI agent application consuming messages *from* its inbox):
    *   Role: `roles/pubsub.subscriber`
    *   Resource: On its specific `agent-sub-<hashed-address>-<consumer-group-id>` subscription.
    *   Role: `roles/pubsub.viewer` (or `roles/pubsub.subscriber` on the DLQ subscription if one is made)
    *   Resource: On its specific `dlq-agent-inbox-<hashed-address>` topic (if the agent needs to be aware of or process its DLQ messages, though this is often an administrative task). Typically, a separate process/administrator would handle DLQ messages.

*   **Provisioning Service Account** (The service/tool responsible for creating and managing these Pub/Sub resources):
    *   Role: `roles/pubsub.editor`
    *   Resource: On the GCP Project. This grants broad permissions.
    *   *Alternatively, for more fine-grained control, a custom role with permissions like:*
        *   `pubsub.topics.create`
        *   `pubsub.topics.get`
        *   `pubsub.topics.update` (potentially, for modifying existing topics)
        *   `pubsub.subscriptions.create`
        *   `pubsub.subscriptions.get`
        *   `pubsub.subscriptions.update` (for settings like DLQ policy)

## 5. Provisioning Script (`pubsub_provisioning.py`)

The `pubsub_provisioning.py` script automates the creation of the topics and subscriptions as described.

### Prerequisites
*   Python 3.7+
*   Google Cloud SDK (`gcloud`) installed and configured.
*   Authenticated to GCP: Run `gcloud auth application-default login`.
*   The `google-cloud-pubsub` Python library installed:
    ```bash
    pip install google-cloud-pubsub
    ```
*   A valid GCP Project ID where resources will be created.

### Usage
The script can be run directly. It contains an example `if __name__ == "__main__":` block that demonstrates how to use the `provision_agent_inbox` function.

```bash
python pubsub_provisioning.py
```
You should modify the `DEFAULT_GCP_PROJECT_ID` in the script or pass the project ID dynamically to the functions if you adapt it for broader use. The example uses a placeholder project ID.

### Example
The `provision_agent_inbox(ai_agent_address, project_id)` function is the primary entry point.

```python
# From pubsub_provisioning.py
if __name__ == "__main__":
    gcp_project_id = "your-actual-gcp-project-id" # Replace this
    sample_agent_address = "agent-support@example.com"

    provision_agent_inbox(sample_agent_address, gcp_project_id)
```

## 6. Manual Verification/Creation with `gcloud`

You can also use `gcloud` commands to manually create, inspect, or verify these resources.

### Setting Project ID
Ensure your `gcloud` is configured for the correct project:
```bash
gcloud config set project your-gcp-project-id
```

Replace `your-gcp-project-id` and other placeholders (like `<hash>`, `<agent-address>`) with actual values.
The `<hash>` should be the SHA-256 hash of the sanitized agent address.

### Creating Topics
**Agent Inbox Topic:**
```bash
# Replace <agent-address> with the actual agent address to generate the topic name
# Example: AGENT_ADDRESS="agent-sales@yourorg.com" (then sanitize and hash it for <hash>)
# TOPIC_NAME="agent-inbox-<hash>"
gcloud pubsub topics create agent-inbox-<hash>
```

**DLQ Topic:**
```bash
# DLQ_TOPIC_NAME="dlq-agent-inbox-<hash>"
gcloud pubsub topics create dlq-agent-inbox-<hash>
```

### Creating Subscription with DLQ
```bash
# Define variables first for clarity
# PROJECT_ID="your-gcp-project-id"
# AGENT_ADDRESS="agent-sales@yourorg.com" (sanitize and hash for <hash>)
# HASHED_ADDRESS="<hash>" # Result of sanitizing and hashing AGENT_ADDRESS
#
# MAIN_TOPIC_NAME="agent-inbox-${HASHED_ADDRESS}"
# DLQ_TOPIC_NAME="dlq-agent-inbox-${HASHED_ADDRESS}"
# SUBSCRIPTION_NAME="agent-sub-${HASHED_ADDRESS}-main-consumer"

gcloud pubsub subscriptions create agent-sub-<hash>-main-consumer \
    --topic agent-inbox-<hash> \
    --dead-letter-topic projects/your-gcp-project-id/topics/dlq-agent-inbox-<hash> \
    --max-delivery-attempts 5 \
    --ack-deadline 10 \
    --message-retention-duration 7d # 7 days (e.g., 7d, 604800s)
```
*   Ensure `your-gcp-project-id` is correctly substituted in the `--dead-letter-topic` path.
*   `--message-retention-duration` format can be like `7d` for days or an integer number of seconds.
*   `--ack-deadline` is in seconds.

### Verifying Resources
**List Topics:**
```bash
gcloud pubsub topics list
```

**Describe a Topic:**
```bash
gcloud pubsub topics describe agent-inbox-<hash>
```

**List Subscriptions:**
```bash
gcloud pubsub subscriptions list
```

**Describe a Subscription:**
```bash
gcloud pubsub subscriptions describe agent-sub-<hash>-main-consumer
```
This command will show the full configuration, including the dead letter policy.
```
