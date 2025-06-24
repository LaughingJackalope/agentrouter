# services/router/message_router_service.py

import asyncio
import json
import uuid
import base64
import time
import os
from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional, List
import json_log_formatter
from dataclasses import dataclass, asdict
from functools import wraps

# Import the new CAMS client
from .cams_client import CAMSClient

# --- Metrics Configuration ---
# This is a simplified metrics collector. In production, you'd use OpenTelemetry or Prometheus client
class MetricsCollector:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
            cls._instance._counters = {}
            cls._instance._histograms = {}
        return cls._instance
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: int = 1):
        """Increment a counter metric with optional labels"""
        key = (name, frozenset((labels or {}).items()))
        self._counters[key] = self._counters.get(key, 0) + value
        
    def record_latency(self, name: str, seconds: float, labels: Optional[Dict[str, str]] = None):
        """Record a latency measurement"""
        key = (name, frozenset((labels or {}).items()))
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(seconds)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return {
            'counters': {
                name: {'labels': dict(labels), 'value': value} 
                for (name, labels), value in self._counters.items()
            },
            'histograms': {
                name: {'labels': dict(labels), 'values': values}
                for (name, labels), values in self._histograms.items()
            }
        }

# Initialize metrics collector
metrics = MetricsCollector()

# --- Logging Configuration ---
class JSONLogFormatter(json_log_formatter.JSONFormatter):
    def json_record(self, message: str, extra: dict, record: logging.LogRecord) -> dict:
        extra['message'] = message
        extra['level'] = record.levelname
        extra['logger'] = record.name
        extra['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add context if present
        if hasattr(record, 'context'):
            extra.update(record.context)
            
        return extra

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add JSON formatter to handler
handler = logging.StreamHandler()
formatter = JSONLogFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Context manager for request context
def log_context(**context):
    """Add context to all log messages within the block"""
    old_context = getattr(logging.getLogRecordFactory(), 'context', {})
    logging.getLogRecordFactory().context = {**old_context, **context}
    
    class ContextManager:
        def __enter__(self):
            pass
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            logging.getLogRecordFactory().context = old_context
            
    return ContextManager()

# Decorator for request timing and error handling
def timed_operation(operation_name: str, **labels):
    """Decorator to time operations and log metrics.
    
    This decorator works with both synchronous and asynchronous functions.
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                status = 'success'
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = 'error'
                    logger.error(f"{operation_name} failed", exc_info=True, 
                               extra={'error': str(e), 'error_type': e.__class__.__name__})
                    raise
                finally:
                    duration = time.time() - start_time
                    metrics.record_latency(
                        f"{operation_name}_duration_seconds", 
                        duration,
                        {**labels, 'status': status}
                    )
                    
                    logger.info(
                        f"{operation_name} completed",
                        extra={
                            'operation': operation_name,
                            'duration_seconds': duration,
                            'status': status,
                            **labels
                        }
                    )
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                status = 'success'
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = 'error'
                    logger.error(f"{operation_name} failed", exc_info=True, 
                               extra={'error': str(e), 'error_type': e.__class__.__name__})
                    raise
                finally:
                    duration = time.time() - start_time
                    metrics.record_latency(
                        f"{operation_name}_duration_seconds", 
                        duration,
                        {**labels, 'status': status}
                    )
                    
                    logger.info(
                        f"{operation_name} completed",
                        extra={
                            'operation': operation_name,
                            'duration_seconds': duration,
                            'status': status,
                            **labels
                        }
                    )
            return sync_wrapper
    return decorator

# Initialize CAMS client
cams_client = CAMSClient()

# For backward compatibility
def getAgentMapping(ai_agent_address: str):
    """Legacy function to maintain compatibility with existing code.
    
    This is a temporary wrapper around the new CAMS client's get_agent_mapping method.
    It should be replaced with direct calls to cams_client.get_agent_mapping in the future.
    """
    import asyncio
    
    async def _get_mapping():
        return await cams_client.get_agent_mapping(ai_agent_address)
        
    try:
        return asyncio.run(_get_mapping())
    except Exception as e:
        logger.error(f"Error in getAgentMapping: {e}")
        return None

# Logging is now configured above with JSON formatter

# --- HTTP Response Helper ---
def create_json_response(data, status_code):
    """
    Helper to create a dictionary representing a JSON response.
    In a real framework (Flask/FastAPI), this would return an actual HTTP response object.
    """
    return {"statusCode": status_code, "body": data}

# --- CAMS Client Wrapper ---
class CAMSClientWrapper:
    """Wrapper around CAMS client to add logging and metrics."""
    
    def __init__(self, cams_client: CAMSClient):
        self.cams_client = cams_client
    
    @timed_operation("cams_lookup", operation="get_agent_mapping")
    async def get_agent_mapping(self, ai_agent_address: str) -> Optional[Dict[str, Any]]:
        """
        Get agent mapping from CAMS.
        
        Args:
            ai_agent_address: The address of the AI agent
            
        Returns:
            Optional[Dict[str, Any]]: The agent mapping if found, None otherwise
        """
        with log_context(ai_agent_address=ai_agent_address):
            logger.info("Looking up agent mapping")
            try:
                result = await self.cams_client.get_agent_mapping(ai_agent_address)
                if result:
                    logger.debug("Agent mapping found", extra={
                        'status': result.get('status', 'UNKNOWN'),
                        'inbox_name': result.get('inboxName')
                    })
                else:
                    logger.warning("Agent mapping not found")
                return result
            except Exception as e:
                logger.error("Failed to get agent mapping", extra={
                    'error': str(e),
                    'error_type': e.__class__.__name__
                })
                raise
    
    @timed_operation("cams_register", operation="register_agent_mapping")
    async def register_agent_mapping(
        self,
        ai_agent_address: str,
        inbox_destination_type: str,
        inbox_name: str,
        description: str = None,
        owner_team: str = None,
        updated_by: str = "router_service"
    ) -> Dict[str, Any]:
        """
        Register a new agent mapping in CAMS.
        
        Args:
            ai_agent_address: The address of the AI agent
            inbox_destination_type: Type of the inbox destination (e.g., GCP_PUBSUB_TOPIC)
            inbox_name: Name of the inbox
            description: Optional description of the agent
            owner_team: Optional owner team
            updated_by: Identifier of who is making the update
            
        Returns:
            Dict[str, Any]: The registered agent mapping
        """
        with log_context(ai_agent_address=ai_agent_address):
            logger.info("Registering agent mapping")
            try:
                return await self.cams_client.register_agent_mapping(
                    ai_agent_address=ai_agent_address,
                    inbox_destination_type=inbox_destination_type,
                    inbox_name=inbox_name,
                    description=description,
                    owner_team=owner_team,
                    updated_by=updated_by
                )
            except Exception as e:
                logger.error("Failed to register agent mapping", extra={
                    'error': str(e),
                    'error_type': e.__class__.__name__
                })
                raise
    
    @timed_operation("cams_update", operation="update_agent_mapping")
    async def update_agent_mapping(
        self,
        ai_agent_address: str,
        updated_by: str = "router_service",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update an agent mapping in CAMS.
        
        Args:
            ai_agent_address: The address of the AI agent
            updated_by: Identifier of who is making the update
            **kwargs: Fields to update
            
        Returns:
            Optional[Dict[str, Any]]: The updated agent mapping if successful, None otherwise
        """
        with log_context(ai_agent_address=ai_agent_address, updated_fields=list(kwargs.keys())):
            logger.info("Updating agent mapping")
            try:
                return await self.cams_client.update_agent_mapping_details(
                    ai_agent_address=ai_agent_address,
                    updated_by=updated_by,
                    **kwargs
                )
            except Exception as e:
                logger.error("Failed to update agent mapping", extra={
                    'error': str(e),
                    'error_type': e.__class__.__name__
                })
                raise
    
    @timed_operation("cams_delete", operation="delete_agent_mapping")
    async def delete_agent_mapping(self, ai_agent_address: str) -> bool:
        """
        Delete an agent mapping from CAMS.
        
        Args:
            ai_agent_address: The address of the AI agent
            
        Returns:
            bool: True if the agent was deleted, False otherwise
        """
        with log_context(ai_agent_address=ai_agent_address):
            logger.info("Deleting agent mapping")
            try:
                return await self.cams_client.delete_agent_mapping(ai_agent_address)
            except Exception as e:
                logger.error("Failed to delete agent mapping", extra={
                    'error': str(e),
                    'error_type': e.__class__.__name__
                })
                raise

# Initialize the CAMS client wrapper
cams_client = CAMSClientWrapper(cams_client)

# --- Pub/Sub Publisher Stub ---
class PubSubPublisher:
    def __init__(self, project_id: str):
        self.project_id = project_id
        # In a real scenario, this would initialize the Google Cloud Pub/Sub client
        # from google.cloud import pubsub_v1
        # self.publisher_client = pubsub_v1.PublisherClient()
        logging.info(f"PubSubPublisher: Initialized for project {project_id} (STUB)")
        self.simulate_failure = False # For testing error handling

    @timed_operation("pubsub_publish", operation="publish_message")
    def publish_message(self, topic_name: str, message_data: dict):
        """
        Publishes a message to the specified Pub/Sub topic.
        This is a stub implementation.
        `topic_name` here is the full topic path like "projects/your-project/topics/your-topic"
        `message_data` is the dictionary conforming to Pub/Sub message structure {"data": "...", "attributes": {...}}
        """
        message_id = str(uuid.uuid4())
        attributes = message_data.get('attributes', {})
        
        log_context_data = {
            'topic_name': topic_name,
            'message_id': message_id,
            'message_size': len(str(message_data.get('data', ''))),
            'ai_agent_address': attributes.get('aiAgentAddress')
        }
        
        with log_context(**log_context_data):
            logger.info("Publishing message to Pub/Sub")
            
            if self.simulate_failure:
                error_msg = f"SIMULATED FAILURE publishing to {topic_name}"
                logger.error(error_msg)
                metrics.increment_counter(
                    "pubsub_publish_errors_total",
                    {
                        'topic_name': topic_name,
                        'error_type': 'simulated_failure',
                        'ai_agent_address': attributes.get('aiAgentAddress')
                    }
                )
                raise Exception(error_msg)

            try:
                # In a real implementation:
                # data_bytes = message_data['data'].encode('utf-8')
                # attributes = message_data['attributes']
                # future = self.publisher_client.publish(topic_name, data=data_bytes, **attributes)
                # message_id = future.result()  # Wait for publish to complete
                
                logger.info("Message published successfully")
                metrics.increment_counter(
                    "pubsub_published_messages_total",
                    {
                        'topic_name': topic_name,
                        'ai_agent_address': attributes.get('aiAgentAddress')
                    }
                )
                return message_id
                
            except Exception as e:
                logger.error("Failed to publish message", extra={
                    'error': str(e),
                    'error_type': e.__class__.__name__
                })
                metrics.increment_counter(
                    "pubsub_publish_errors_total",
                    {
                        'topic_name': topic_name,
                        'error_type': e.__class__.__name__,
                        'ai_agent_address': attributes.get('aiAgentAddress')
                    }
                )
                raise

# Initialize a conceptual Pub/Sub publisher
# In a real app, project_id would come from config
pubsub_publisher = PubSubPublisher(project_id="your-gcp-project")


# --- Core Message Ingestion Logic ---
def handle_message_ingestion(request_payload: dict):
    """
    Handles the ingestion of an incoming message.
    """
    logging.info(f"handle_message_ingestion: Received request: {request_payload}")

    # 1. Generate messageId
    message_id = str(uuid.uuid4())
    logging.info(f"Generated messageId: {message_id}")

    # 2. Input Validation
    ai_agent_address = request_payload.get("aiAgentAddress")
    payload_content = request_payload.get("payload")

    if not ai_agent_address or not isinstance(ai_agent_address, str) or not ai_agent_address.strip():
        logging.warning("Validation failed: aiAgentAddress is missing or invalid.")
        return create_json_response(
            {"errorCode": "INVALID_REQUEST", "message": "aiAgentAddress is required and must be a non-empty string."},
            400
        )

    if payload_content is None: # Checking for None explicitly, as {} is a valid payload
        logging.warning("Validation failed: payload is missing.")
        return create_json_response(
            {"errorCode": "INVALID_REQUEST", "message": "payload is required."},
            400
        )

    if not isinstance(payload_content, dict):
        logging.warning("Validation failed: payload must be a JSON object.")
        return create_json_response(
            {"errorCode": "INVALID_REQUEST", "message": "payload must be a JSON object."},
            400
        )

    # 3. CAMS Lookup
    agent_mapping = cams_client.get_agent_mapping(ai_agent_address)

    # 4. Conditional Routing Logic
    if not agent_mapping:
        logging.warning(f"Agent not found in CAMS: {ai_agent_address}")
        return create_json_response(
            {"errorCode": "AGENT_NOT_FOUND", "message": f"AI Agent Address '{ai_agent_address}' not found."},
            404
        )

    if agent_mapping.get("status") == "INACTIVE":
        logging.warning(f"Agent '{ai_agent_address}' is INACTIVE.")
        return create_json_response(
            {"errorCode": "AGENT_INACTIVE", "message": f"AI Agent '{ai_agent_address}' is currently inactive."},
            404 # As per requirements, 404 for inactive agent
        )

    if agent_mapping.get("status") != "ACTIVE":
        logging.error(f"Agent '{ai_agent_address}' has an unknown status: {agent_mapping.get('status')}")
        return create_json_response(
            {"errorCode": "INTERNAL_SERVER_ERROR", "message": f"AI Agent '{ai_agent_address}' has an unknown status."},
            500
        )

    # Scenario C: Agent Found and ACTIVE
    pubsub_topic_name = agent_mapping.get("inboxName")
    if not pubsub_topic_name:
        logging.error(f"Agent '{ai_agent_address}' is ACTIVE but has no inboxName defined in CAMS.")
        return create_json_response(
            {"errorCode": "CONFIG_ERROR", "message": "Agent configuration error: inboxName missing."},
            500
        )

    # 5. Transform to Pub/Sub Message
    try:
        # 5.1. Prepare 'data' field (Base64 encode the original payload)
        payload_string = json.dumps(payload_content)
        payload_base64_bytes = base64.b64encode(payload_string.encode('utf-8'))
        pubsub_data = payload_base64_bytes.decode('utf-8')

        # 5.2. Prepare 'attributes'
        pubsub_attributes = {
            "messageId": message_id,
            "aiAgentAddress": ai_agent_address,
            "timestampPublished": datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
            "contentType": "application/json" # Fixed for MVP as per Task 01
        }

        sender_metadata = request_payload.get("senderMetadata", {})
        if isinstance(sender_metadata, dict):
            if "serviceName" in sender_metadata:
                pubsub_attributes["senderId"] = sender_metadata["serviceName"]
            if "correlationId" in sender_metadata:
                pubsub_attributes["correlationId"] = sender_metadata["correlationId"]
            if "senderProvidedMessageId" in sender_metadata:
                pubsub_attributes["senderProvidedMessageId"] = sender_metadata["senderProvidedMessageId"]

        transformed_message = {
            "data": pubsub_data,
            "attributes": pubsub_attributes
        }
        logging.info(f"Transformed message for Pub/Sub: {transformed_message['attributes']}")

    except Exception as e:
        logging.error(f"Error during message transformation: {e}", exc_info=True)
        return create_json_response(
            {"errorCode": "TRANSFORMATION_ERROR", "message": "Failed to transform message for Pub/Sub."},
            500
        )

    # 6. Publish to Pub/Sub
    try:
        pubsub_publisher.publish_message(pubsub_topic_name, transformed_message)
        logging.info(f"Message {message_id} successfully published to topic {pubsub_topic_name} for agent {ai_agent_address}")
    except Exception as e:
        logging.error(f"Failed to publish message {message_id} to Pub/Sub topic {pubsub_topic_name}: {e}", exc_info=True)
        return create_json_response(
            {"errorCode": "PUB_SUB_ERROR", "message": "Failed to publish message to Pub/Sub."},
            500
        )

    # 7. Return Success
    return create_json_response({"messageId": message_id}, 202)


# --- Example Usage / Basic Test Cases ---
if __name__ == "__main__":
    print("--- Message Router Service: Test Scenarios ---")

    # Scenario 1: Valid Request
    print("\n[Scenario 1: Valid Request]")
    valid_request = {
      "aiAgentAddress": "active-agent@example.com",
      "payload": {"command": "processData", "value": 42},
      "senderMetadata": {
        "serviceName": "CRM_System",
        "correlationId": "crm-corr-123",
        "senderProvidedMessageId": "crm-msg-abc"
      }
    }
    response = handle_message_ingestion(valid_request)
    print(f"Response: {response}")
    assert response["statusCode"] == 202
    assert "messageId" in response["body"]

    # Scenario 2: Agent Not Found
    print("\n[Scenario 2: Agent Not Found]")
    not_found_request = {
      "aiAgentAddress": "unknown-agent@example.com",
      "payload": {"command": "doSomething"}
    }
    response = handle_message_ingestion(not_found_request)
    print(f"Response: {response}")
    assert response["statusCode"] == 404
    assert response["body"]["errorCode"] == "AGENT_NOT_FOUND"

    # Scenario 3: Inactive Agent
    print("\n[Scenario 3: Inactive Agent]")
    inactive_agent_request = {
      "aiAgentAddress": "inactive-agent@example.com",
      "payload": {"command": "doSomethingElse"}
    }
    response = handle_message_ingestion(inactive_agent_request)
    print(f"Response: {response}")
    assert response["statusCode"] == 404 # As per requirement for inactive
    assert response["body"]["errorCode"] == "AGENT_INACTIVE"

    # Scenario 4: Missing aiAgentAddress
    print("\n[Scenario 4: Missing aiAgentAddress]")
    missing_address_request = {
      # "aiAgentAddress": "active-agent@example.com",
      "payload": {"command": "processData"}
    }
    response = handle_message_ingestion(missing_address_request)
    print(f"Response: {response}")
    assert response["statusCode"] == 400
    assert response["body"]["errorCode"] == "INVALID_REQUEST"

    # Scenario 5: Missing payload
    print("\n[Scenario 5: Missing payload]")
    missing_payload_request = {
      "aiAgentAddress": "active-agent@example.com"
      # "payload": {"command": "processData"}
    }
    response = handle_message_ingestion(missing_payload_request)
    print(f"Response: {response}")
    assert response["statusCode"] == 400
    assert response["body"]["errorCode"] == "INVALID_REQUEST"

    # Scenario 5b: Payload not a JSON object
    print("\n[Scenario 5b: Payload not a JSON object]")
    invalid_payload_request = {
      "aiAgentAddress": "active-agent@example.com",
      "payload": "not a dict"
    }
    response = handle_message_ingestion(invalid_payload_request)
    print(f"Response: {response}")
    assert response["statusCode"] == 400
    assert response["body"]["errorCode"] == "INVALID_REQUEST"
    assert "payload must be a JSON object" in response["body"]["message"]


    # Scenario 6: Pub/Sub Publish Error
    print("\n[Scenario 6: Pub/Sub Publish Error]")
    pubsub_publisher.simulate_failure = True # Trigger failure in stub
    pubsub_fail_request = {
      "aiAgentAddress": "active-agent@example.com",
      "payload": {"command": "criticalTask"},
      "senderMetadata": {"serviceName": "CriticalService"}
    }
    response = handle_message_ingestion(pubsub_fail_request)
    print(f"Response: {response}")
    assert response["statusCode"] == 500
    assert response["body"]["errorCode"] == "PUB_SUB_ERROR"
    pubsub_publisher.simulate_failure = False # Reset simulation

    # Scenario 7: Valid request with minimal senderMetadata
    print("\n[Scenario 7: Valid Request, minimal senderMetadata]")
    valid_request_minimal_meta = {
      "aiAgentAddress": "active-agent@example.com",
      "payload": {"data": "sample"},
      "senderMetadata": {} # Empty but present
    }
    response = handle_message_ingestion(valid_request_minimal_meta)
    print(f"Response: {response}")
    assert response["statusCode"] == 202
    assert "messageId" in response["body"]

    # Scenario 8: Valid request, no senderMetadata
    print("\n[Scenario 8: Valid Request, no senderMetadata]")
    valid_request_no_meta = {
      "aiAgentAddress": "active-agent@example.com",
      "payload": {"data": "another sample"}
    }
    response = handle_message_ingestion(valid_request_no_meta)
    print(f"Response: {response}")
    assert response["statusCode"] == 202
    assert "messageId" in response["body"]

    # Scenario 9: CAMS returns active agent but no inboxName (config error)
    print("\n[Scenario 9: Agent Active but no inboxName in CAMS mapping]")
    # Temporarily modify mock CAMS for this test case

    # Declare global intent before assignment if we are rebinding the global name
    # However, the issue is more about how the functions are defined and used.
    # Let's ensure the global cams_client uses the modified getAgentMapping.

    # Store the original method from the global cams_client instance
    original_cams_client_get_mapping_method = cams_client.get_agent_mapping

    def mock_cams_get_mapping_for_no_inbox_test(ai_agent_address: str):
        if ai_agent_address == "active-no-inbox@example.com":
            logging.info("MOCK CAMS (Scenario 9): Returning agent with no inboxName")
            return {
                "aiAgentAddress": ai_agent_address,
                "status": "ACTIVE",
                "inboxName": None, # Missing inboxName
                # other fields can be minimal for this test
            }
        # Fallback for other agents if necessary, though this test is specific
        return original_cams_client_get_mapping_method(ai_agent_address)

    # Temporarily replace the method on the global cams_client instance
    cams_client.get_agent_mapping = mock_cams_get_mapping_for_no_inbox_test

    try:
        no_inbox_request = {
            "aiAgentAddress": "active-no-inbox@example.com",
            "payload": {"data": "test"}
        }
        response = handle_message_ingestion(no_inbox_request)
        print(f"Response: {response}")
        assert response["statusCode"] == 500
        assert response["body"]["errorCode"] == "CONFIG_ERROR", f"Expected CONFIG_ERROR, got {response['body'].get('errorCode')}"
    finally:
        # Restore the original method on the global cams_client instance
        cams_client.get_agent_mapping = original_cams_client_get_mapping_method


    print("\n--- All test scenarios completed. ---")
