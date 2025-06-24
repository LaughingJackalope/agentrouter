# Windsurf Task 09: Implement DLQ Monitoring & Alerting

## 1. Task Objective

This task is to define and implement the necessary components for monitoring messages that land in the Dead Letter Queues (DLQs) of our AI Agent inboxes and to set up basic alerting mechanisms for these events. The goal is to ensure visibility and prompt action for messages that fail processing.

This aligns with **Phase 2: Management & Operational Readiness**, specifically **"Implement DLQ Monitoring & Alerting"** in our Pragmatic Development Roadmap.

## 2. Context & Rationale

We've designed our system with Dead Letter Queues for Pub/Sub subscriptions (Task 03). While DLQs prevent message loss, they represent messages that could not be successfully processed by an AI Agent after multiple retries. It's critical to:
* **Gain Visibility:** Know when messages enter a DLQ.
* **Identify Patterns:** Understand why messages are failing.
* **Enable Action:** Allow for manual intervention, re-processing, or bug fixing based on DLQ content.
* **Prevent Accumulation:** Avoid a build-up of unaddressed failed messages.

This task will primarily focus on setting up the conceptual framework for monitoring and basic alerting, leveraging existing logging and metrics capabilities where possible.

## 3. Detailed Requirements

Windsurf should focus on defining how DLQ events are captured and surfaced, rather than building a full-fledged message re-processing pipeline (which would be a later phase).

### 3.1. DLQ Event Logging & Metrics

* **Logging DLQ Events:**
    * Whenever a message is moved to a DLQ (Pub/Sub natively handles this, but we need to ensure our system observes it). Since the Router publishes messages and agents consume them, the Router won't directly observe messages moving to DLQ unless it's designed to subscribe to DLQs (which it isn't).
    * Instead, focus on how we can confirm that messages are reaching the DLQ. Pub/Sub emits metrics for messages in DLQ.
    * **Focus Point:** Within the `services/router/` context, ensure that our `pubsub_publisher` logs any *publish failures* (which, if persistent, would eventually lead to a DLQ if retried externally by an agent, or if an agent explicitly NACKs messages to DLQ). More directly, focus on the Pub/Sub metrics for DLQ volume.
* **Metrics for DLQs:**
    * **`pubsub_dlq_message_count` (Gauge):** The current number of messages in each DLQ. This is a crucial metric, directly exposed by GCP Pub/Sub. Windsurf should document how to observe this via Google Cloud Monitoring.
        * Labels: `dlq_topic_name`, `ai_agent_address` (derived).
    * **`pubsub_dlq_messages_added_total` (Counter):** The total number of messages that have *entered* a DLQ. This is also a GCP Pub/Sub metric. Windsurf should document how to observe this.
        * Labels: `dlq_topic_name`, `ai_agent_address` (derived).

### 3.2. Conceptual Alerting Strategy

Outline how alerts would be set up based on DLQ metrics.

* **Alerting Triggers:**
    * **DLQ Message Count Threshold:** Alert if the `pubsub_dlq_message_count` for any DLQ exceeds a certain threshold (e.g., 1 or 5 messages) for a sustained period. This indicates an unhandled failure.
    * **DLQ Message Ingress Rate:** Alert if `pubsub_dlq_messages_added_total` shows a sudden spike or sustained rate, indicating a new, widespread issue.
* **Notification Channels:** Document conceptual notification channels (e.g., PagerDuty, Slack, email via Cloud Monitoring alerts).
* **Alert Severity:** Define different severities based on the thresholds (e.g., WARNING for a few messages, CRITICAL for a high volume).

### 3.3. Integration Points (Documentation Focused)

Since our code doesn't directly interact with DLQs in a way that *moves* messages to them (Pub/Sub handles this), Windsurf's task is primarily about documenting how to *monitor* what Pub/Sub already exposes.

* Document how `aiAgentAddress` maps to `dlq_topic_name` for monitoring purposes, leveraging the naming convention established in Task 03.
* Provide conceptual `gcloud` commands or Cloud Monitoring API examples for querying these metrics.

## 4. Dependencies

* **Jules Task 03 Output:** Pub/Sub Topic and Subscription setup, especially DLQ configuration and naming conventions.
* **Windsurf Task 06 Output:** Comprehensive Logging & Metrics foundation (for context on how metrics are generally handled, though DLQ metrics are largely external).

## 5. Expected Output from Windsurf

Upon completion, Windsurf should provide:

* **`docs/observability/dlq_monitoring_guide.md`**: A new markdown document detailing:
    * The importance of DLQ monitoring.
    * The key GCP Pub/Sub metrics to observe for DLQs (`pubsub_dlq_message_count`, `pubsub_dlq_messages_added_total`).
    * Conceptual alerting strategies (thresholds, spikes).
    * Examples of how to identify the DLQ topic for a given `aiAgentAddress`.
    * Conceptual `gcloud` commands or Cloud Monitoring dashboard setup steps.
    * Any recommended manual inspection steps for messages in DLQs (e.g., using Pub/Sub UI or `gcloud`).
* **Updates to `docs/observability/observability_guide.md`**: Briefly reference the new `dlq_monitoring_guide.md` and ensure DLQ metrics are included in the overall observability picture.

## 6. Output Location

* New document: `docs/observability/dlq_monitoring_guide.md`
* Updated document: `docs/observability/observability_guide.md`

---

This task will ensure we have proactive mechanisms to address failed messages. Let me know if this is clear for Windsurf, Pilot!