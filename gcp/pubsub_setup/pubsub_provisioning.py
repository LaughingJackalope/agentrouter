# -*- coding: utf-8 -*-
"""
Provisions Google Cloud Pub/Sub topics and subscriptions for AI Agent inboxes.

This script provides functions to:
- Generate standardized names for topics, subscriptions, and Dead Letter Queues (DLQs).
- Create Pub/Sub topics for agent inboxes and their associated DLQs.
- Create Pub/Sub pull subscriptions with DLQ configuration.
"""

import hashlib
import re
from google.cloud import pubsub_v1
from google.api_core import exceptions as google_exceptions

# Placeholder for the GCP Project ID. In a real scenario, this would be
# dynamically passed or configured.
DEFAULT_GCP_PROJECT_ID = "your-gcp-project-id"

def _sanitize_and_hash_address(ai_agent_address: str) -> str:
    """
    Sanitizes an AI agent address and returns its SHA-256 hash.

    Sanitization steps:
    1. Convert to lowercase.
    2. Replace non-alphanumeric characters (anything not a-z, 0-9) with hyphens.
       This is a common practice before hashing to ensure consistency.
       The task description: "convert the aiAgentAddress to lowercase,
       replace non-alphanumeric characters with hyphens, and then take a
       SHA-256 hash of the result".

    Args:
        ai_agent_address: The AI agent's address (e.g., "agent-sales@yourorg.com").

    Returns:
        A string representing the hexadecimal SHA-256 hash of the sanitized address.
    """
    sanitized_address = ai_agent_address.lower()
    # Replace any character that is not a lowercase letter, number, or hyphen with a hyphen
    sanitized_address = re.sub(r"[^a-z0-9\-]", "-", sanitized_address)
    # Collapse multiple hyphens into one
    sanitized_address = re.sub(r"-+", "-", sanitized_address)
    # Remove leading/trailing hyphens that might result from replacements
    sanitized_address = sanitized_address.strip('-')

    hasher = hashlib.sha256()
    hasher.update(sanitized_address.encode('utf-8'))
    return hasher.hexdigest()

def generate_topic_name(ai_agent_address: str) -> str:
    """
    Generates a Pub/Sub topic name for an AI agent's inbox.

    Format: agent-inbox-<aiAgentAddress-sanitized-hash>

    Args:
        ai_agent_address: The AI agent's address.

    Returns:
        The generated Pub/Sub topic name.
    """
    hashed_address = _sanitize_and_hash_address(ai_agent_address)
    return f"agent-inbox-{hashed_address}"

def generate_dlq_topic_name(ai_agent_address: str) -> str:
    """
    Generates a Pub/Sub topic name for the Dead Letter Queue (DLQ)
    associated with an AI agent's inbox.

    Format: dlq-agent-inbox-<aiAgentAddress-sanitized-hash>

    Args:
        ai_agent_address: The AI agent's address.

    Returns:
        The generated DLQ topic name.
    """
    hashed_address = _sanitize_and_hash_address(ai_agent_address)
    return f"dlq-agent-inbox-{hashed_address}"

def generate_subscription_name(ai_agent_address: str, consumer_group_id: str = "main-consumer") -> str:
    """
    Generates a Pub/Sub subscription name for an AI agent's inbox.

    Format: agent-sub-<aiAgentAddress-sanitized-hash>-<consumer-group-id>

    Args:
        ai_agent_address: The AI agent's address.
        consumer_group_id: Identifier for the consumer group (default: "main-consumer").

    Returns:
        The generated Pub/Sub subscription name.
    """
    hashed_address = _sanitize_and_hash_address(ai_agent_address)
    return f"agent-sub-{hashed_address}-{consumer_group_id}"

def create_topic_if_not_exists(project_id: str, topic_name: str) -> str:
    """
    Creates a Pub/Sub topic if it doesn't already exist.

    Args:
        project_id: The GCP project ID.
        topic_name: The name for the topic.

    Returns:
        The fully qualified topic path.
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)

    try:
        publisher.create_topic(request={"name": topic_path})
        print(f"Topic created: {topic_path}")
    except google_exceptions.AlreadyExists:
        print(f"Topic already exists: {topic_path}")
    except Exception as e:
        print(f"An error occurred while creating topic {topic_path}: {e}")
        raise
    return topic_path

def create_subscription_with_dlq(
    project_id: str,
    topic_path: str,
    subscription_name: str,
    dlq_topic_path: str
) -> str:
    """
    Creates a Pub/Sub pull subscription with a Dead Letter Queue (DLQ) configuration.

    Args:
        project_id: The GCP project ID.
        topic_path: The fully qualified path of the main topic to subscribe to.
        subscription_name: The name for the subscription.
        dlq_topic_path: The fully qualified path of the DLQ topic.

    Returns:
        The fully qualified subscription path.
    """
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_name)

    dead_letter_policy = pubsub_v1.types.DeadLetterPolicy(
        dead_letter_topic=dlq_topic_path,
        max_delivery_attempts=5,
    )

    # Default acknowledgement deadline is 10 seconds.
    # Default message retention duration is 7 days.
    # These are standard defaults and often don't need to be explicitly set
    # unless a deviation from the default is required.
    # The google-cloud-pubsub library will use these defaults if not specified.

    request = {
        "name": subscription_path,
        "topic": topic_path,
        "dead_letter_policy": dead_letter_policy,
        "ack_deadline_seconds": 10, # Explicitly set as per requirements
        "retain_acked_messages": False, # Standard behavior
        "message_retention_duration": {"seconds": 60 * 60 * 24 * 7} # 7 days
    }

    try:
        subscriber.create_subscription(request=request)
        print(f"Subscription created: {subscription_path} for topic {topic_path}")
        print(f"  - DLQ Topic: {dlq_topic_path}")
        print(f"  - Max Delivery Attempts: {dead_letter_policy.max_delivery_attempts}")
        print(f"  - Ack Deadline: 10 seconds")
        print(f"  - Message Retention: 7 days")
    except google_exceptions.AlreadyExists:
        print(f"Subscription already exists: {subscription_path}")
    except Exception as e:
        print(f"An error occurred while creating subscription {subscription_path}: {e}")
        raise
    return subscription_path

def provision_agent_inbox(ai_agent_address: str, project_id: str):
    """
    Provisions a complete Pub/Sub inbox (topic, DLQ topic, subscription) for an AI agent.

    Args:
        ai_agent_address: The AI agent's address.
        project_id: The GCP project ID.
    """
    print(f"\nProvisioning Pub/Sub resources for agent: {ai_agent_address} in project: {project_id}")

    # Generate names
    agent_topic_name = generate_topic_name(ai_agent_address)
    dlq_topic_name_str = generate_dlq_topic_name(ai_agent_address)
    subscription_name_str = generate_subscription_name(ai_agent_address)

    # Create DLQ topic first (as it's referenced by the subscription)
    print(f"\nStep 1: Ensure DLQ topic exists ({dlq_topic_name_str})")
    dlq_topic_path = create_topic_if_not_exists(project_id, dlq_topic_name_str)

    # Create main agent inbox topic
    print(f"\nStep 2: Ensure main agent inbox topic exists ({agent_topic_name})")
    agent_topic_path = create_topic_if_not_exists(project_id, agent_topic_name)

    # Create subscription with DLQ
    print(f"\nStep 3: Ensure subscription with DLQ exists ({subscription_name_str})")
    create_subscription_with_dlq(
        project_id,
        agent_topic_path,
        subscription_name_str,
        dlq_topic_path
    )
    print(f"\nSuccessfully provisioned resources for {ai_agent_address}")

if __name__ == "__main__":
    # Example Usage:
    # Replace with your actual project ID and desired agent addresses
    gcp_project_id = DEFAULT_GCP_PROJECT_ID
    sample_agent_address = "agent-sales.support@example-org.com"
    another_agent_address = "agent-billing_department+extra@another-entity.co.uk"

    print("Starting Pub/Sub provisioning script example...")
    print("-----------------------------------------------")
    print(f"Using GCP Project ID: {gcp_project_id}")
    print("Note: This script will attempt to interact with Google Cloud Pub/Sub.")
    print("Ensure you have authenticated with 'gcloud auth application-default login'")
    print("and the 'google-cloud-pubsub' library is installed.")
    print("-----------------------------------------------\n")

    # Demonstrate name generation
    print("Name Generation Examples:")
    test_address = "test-agent@example.com"
    print(f"  For Address: {test_address}")
    print(f"    Topic Name: {generate_topic_name(test_address)}")
    print(f"    DLQ Topic Name: {generate_dlq_topic_name(test_address)}")
    print(f"    Subscription Name: {generate_subscription_name(test_address)}")
    print(f"    Subscription Name (custom consumer): {generate_subscription_name(test_address, consumer_group_id='analytics-v1')}")


    # Provision for the sample agent
    # In a real environment, these calls would be triggered by an agent registration process.
    # For this script, we simulate it.
    # IMPORTANT: Running this will attempt to create resources in your GCP project.
    #            Comment out if you don't want to create actual resources.
    try:
        provision_agent_inbox(sample_agent_address, gcp_project_id)
        provision_agent_inbox(another_agent_address, gcp_project_id)
    except Exception as e:
        print(f"\nAn error occurred during provisioning: {e}")
        print("Please ensure your GCP environment is configured correctly.")

    print("\n-----------------------------------------------")
    print("Pub/Sub provisioning script example finished.")

    # A note on sanitization for topic names:
    # Pub/Sub topic names must start with a letter, and contain only letters (a-z, A-Z),
    # numbers (0-9), dashes (-), periods (.), underscores (_), tildes (~), plus signs (+),
    # and percent signs (%). They must be between 3 and 255 characters long.
    # The hashing approach helps ensure uniqueness and avoids most character issues.
    # The chosen names (e.g., "agent-inbox-<hash>") conform to these rules as hashes are
    # hex strings and hyphens are allowed.
    # The prefix "agent-inbox-" starts with a letter.
    # The length of SHA256 hex is 64 chars. Prefixes add ~15-20 chars. Total length is well within limits.
    #
    # Sanitization in _sanitize_and_hash_address:
    # The task: "convert the aiAgentAddress to lowercase, replace non-alphanumeric characters with hyphens,
    # and then take a SHA-256 hash of the result".
    # My implementation of _sanitize_and_hash_address:
    # 1. `sanitized_address = ai_agent_address.lower()` - converts to lowercase.
    # 2. `sanitized_address = re.sub(r"[^a-z0-9\-]", "-", sanitized_address)` - replaces non-alphanumeric
    #    (excluding hyphen itself as it's a common separator) with hyphens.
    #    This means `.` and `@` in emails will become hyphens.
    #    e.g., `agent-sales.support@example-org.com` -> `agent-sales-support-example-org-com`
    # 3. `sanitized_address = re.sub(r"-+", "-", sanitized_address)` - collapses multiple hyphens.
    # 4. `sanitized_address = sanitized_address.strip('-')` - removes leading/trailing hyphens.
    # This sanitized string is then hashed. This seems to align with the requirement.
    # The hash itself will be alphanumeric, so it's safe for Pub/Sub names.
    # The prefixes like "agent-inbox-" are also safe.
```
