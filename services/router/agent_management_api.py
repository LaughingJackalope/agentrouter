# services/router/agent_management_api.py
# API handlers for Agent Address Management

from flask import Flask, request, jsonify
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Conceptual CAMS Client ---
# This is a placeholder for the actual CAMS client.
# Its methods are based on services/cams/cams_api_pseudo.py

class CAMSClientPseudo:
    def registerAgentMapping(self, aiAgentAddress: str, inboxDestinationType: str, inboxName: str,
                             description: str = None, ownerTeam: str = None, updatedBy: str = "router_service"):
        print(f"CAMSClientPseudo.registerAgentMapping called with: {aiAgentAddress}, {inboxDestinationType}, {inboxName}, {description}, {ownerTeam}")
        # Simulate CAMS behavior
        if aiAgentAddress == "existing@example.com": # Simulate conflict
            raise ValueError(f"Error: Agent with address '{aiAgentAddress}' already exists.")

        # Simulate successful registration
        return {
            "aiAgentAddress": aiAgentAddress,
            "inboxDestinationType": inboxDestinationType,
            "inboxName": inboxName,
            "status": "ACTIVE", # Default status
            "registrationTimestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "lastUpdatedTimestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "description": description,
            "ownerTeam": ownerTeam,
            "updatedBy": updatedBy
        }

    def getAgentMapping(self, aiAgentAddress: str):
        print(f"CAMSClientPseudo.getAgentMapping called with: {aiAgentAddress}")
        if aiAgentAddress == "notfound@example.com":
            return None
        if aiAgentAddress == "existing@example.com" or aiAgentAddress == "test@example.com":
            return {
                "aiAgentAddress": aiAgentAddress,
                "inboxDestinationType": "GCP_PUBSUB_TOPIC",
                "inboxName": f"projects/your-gcp-project/topics/{aiAgentAddress.split('@')[0]}-inbox",
                "status": "ACTIVE",
                "registrationTimestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "lastUpdatedTimestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "description": "An existing agent",
                "ownerTeam": "Test Team"
            }
        return None # Default to not found

    def updateAgentStatus(self, aiAgentAddress: str, newStatus: str, updatedBy: str = "router_service"):
        print(f"CAMSClientPseudo.updateAgentStatus called with: {aiAgentAddress}, {newStatus}")
        # Simulate CAMS behavior
        current_mapping = self.getAgentMapping(aiAgentAddress)
        if not current_mapping: # Should be caught by updateAgentMappingDetails, but good for direct calls
            # raise ValueError(f"Agent {aiAgentAddress} not found for status update.")
             return False # Adhering to prior return style for this specific mock

        current_mapping["status"] = newStatus
        current_mapping["lastUpdatedTimestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current_mapping["updatedBy"] = updatedBy
        return current_mapping # Return updated mapping on success

    def updateAgentInbox(self, aiAgentAddress: str, newInboxDestinationType: str, newInboxName: str, updatedBy: str = "router_service"):
        print(f"CAMSClientPseudo.updateAgentInbox called with: {aiAgentAddress}, {newInboxDestinationType}, {newInboxName}")
        current_mapping = self.getAgentMapping(aiAgentAddress)
        if not current_mapping: # Should be caught by updateAgentMappingDetails
            # raise ValueError(f"Agent {aiAgentAddress} not found for inbox update.")
            return False

        current_mapping["inboxDestinationType"] = newInboxDestinationType
        current_mapping["inboxName"] = newInboxName
        current_mapping["lastUpdatedTimestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current_mapping["updatedBy"] = updatedBy
        return current_mapping

    def updateAgentMappingDetails(self, aiAgentAddress: str, updatedBy: str = "router_service", **kwargs):
        print(f"CAMSClientPseudo.updateAgentMappingDetails called for {aiAgentAddress} with {kwargs}")
        # Simulate CAMS updateAgentMappingDetails behavior
        # This is a simplified mock. The real one is in cams_api_pseudo.py
        existing_mapping = self.getAgentMapping(aiAgentAddress)
        if not existing_mapping:
            # In a real scenario, CAMS client would raise an error or return specific code
            # For this mock, let's align with what the API handler might expect from a more robust client.
            # Raising an error that the API handler can catch is often better.
            # However, the pseudo CAMS client's updateAgentMappingDetails returns None if not found.
            return None

        # Validate status if provided in kwargs
        if "status" in kwargs and kwargs["status"] not in ["ACTIVE", "INACTIVE"]:
            raise ValueError("Invalid status value. Must be 'ACTIVE' or 'INACTIVE'.")

        # Apply updates
        for key, value in kwargs.items():
            if key in existing_mapping: # Only update valid fields
                existing_mapping[key] = value

        existing_mapping["lastUpdatedTimestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        existing_mapping["updatedBy"] = updatedBy
        return existing_mapping

    def deleteAgentMapping(self, aiAgentAddress: str):
        print(f"CAMSClientPseudo.deleteAgentMapping called with: {aiAgentAddress}")
        if aiAgentAddress == "notfound@example.com":
            return False # Simulate not found
        return True # Simulate success

# Instantiate the conceptual CAMS client
cams_client = CAMSClientPseudo()

# Initialize Flask app (conceptual, not running a server here)
app = Flask(__name__)

# Import health check routes and metrics
from agent_health_check_api import register_health_check_routes
from message_router_service import MetricsCollector

# --- API Endpoints ---
# Base path: /v1/agent-inboxes

@app.route('/v1/agent-inboxes', methods=['POST'])
def register_agent_mapping():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        aiAgentAddress = data.get("aiAgentAddress")
        inboxDestinationType = data.get("inboxDestinationType")
        inboxName = data.get("inboxName")
        description = data.get("description")
        ownerTeam = data.get("ownerTeam")

        if not all([aiAgentAddress, inboxDestinationType, inboxName]):
            return jsonify({"error": "Missing required fields: aiAgentAddress, inboxDestinationType, inboxName"}), 400

        new_mapping = cams_client.registerAgentMapping(
            aiAgentAddress=aiAgentAddress,
            inboxDestinationType=inboxDestinationType,
            inboxName=inboxName,
            description=description,
            ownerTeam=ownerTeam
        )
        return jsonify(new_mapping), 201

    except ValueError as ve: # Handles duplicate agent address from CAMS client
        if "already exists" in str(ve):
            return jsonify({"error": str(ve)}), 409
        return jsonify({"error": str(ve)}), 400 # Other ValueErrors from CAMS client
    except Exception as e:
        # Log the exception e
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/v1/agent-inboxes/<path:aiAgentAddress>', methods=['GET'])
def retrieve_agent_mapping(aiAgentAddress):
    if not aiAgentAddress:
        return jsonify({"error": "aiAgentAddress path parameter is required"}), 400

    mapping = cams_client.getAgentMapping(aiAgentAddress)
    if mapping:
        return jsonify(mapping), 200
    else:
        return jsonify({"error": f"Agent mapping not found for {aiAgentAddress}"}), 404

@app.route('/v1/agent-inboxes/<path:aiAgentAddress>', methods=['PUT'])
def update_agent_mapping(aiAgentAddress):
    if not aiAgentAddress:
        return jsonify({"error": "aiAgentAddress path parameter is required"}), 400

    data = request.get_json()
    if not data: # Empty payload is not necessarily an error if nothing is to be changed.
        return jsonify({"message": "No update fields provided in payload."}), 400 # Or 200 if we want to allow empty PUTs as no-op

    # Check if agent exists by attempting to get it first.
    # The CAMS client's updateAgentMappingDetails also checks, but this provides a clearer 404.
    if not cams_client.getAgentMapping(aiAgentAddress):
         return jsonify({"error": f"Agent mapping not found for {aiAgentAddress}"}), 404

    # Prepare kwargs for the CAMS client from the request data
    update_kwargs = {}
    allowed_fields_for_update = ["inboxDestinationType", "inboxName", "description", "ownerTeam", "status"]

    for field in allowed_fields_for_update:
        if field in data:
            update_kwargs[field] = data[field]

    if not update_kwargs:
        return jsonify({"message": "No valid update fields provided in payload."}), 400 # Or 200 if we want to allow PUT with no relevant fields as no-op

    try:
        # Call the new generic update function in CAMS client
        updated_mapping = cams_client.updateAgentMappingDetails(
            aiAgentAddress=aiAgentAddress,
            updatedBy="router_service/PUT", # Add more specific updatedBy
            **update_kwargs
        )

        if updated_mapping:
            return jsonify(updated_mapping), 200
        else:
            # This case might be hit if CAMS's internal update logic fails after finding the agent,
            # or if the CAMS client returns None for other reasons (e.g. not found by its own check).
            # Given the pre-check, this implies an issue during the update process itself.
            return jsonify({"error": f"Failed to update agent mapping for {aiAgentAddress}. Agent might no longer exist or an internal error occurred."}), 500

    except ValueError as ve: # Catch validation errors from CAMS client (e.g., invalid status)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # Log the exception e
        print(f"Unexpected error during agent update: {e}") # Basic logging
        return jsonify({"error": "An unexpected error occurred during update"}), 500


@app.route('/v1/agent-inboxes/<path:aiAgentAddress>', methods=['DELETE'])
def delete_agent_mapping_handler(aiAgentAddress): # Renamed to avoid conflict with cams_client.deleteAgentMapping
    if not aiAgentAddress:
        return jsonify({"error": "aiAgentAddress path parameter is required"}), 400

    # Check if mapping exists before attempting delete for 404
    # Note: cams_client.deleteAgentMapping also returns False if not found,
    # but specific 404 before call is good practice.
    if not cams_client.getAgentMapping(aiAgentAddress):
        return jsonify({"error": f"Agent mapping not found for {aiAgentAddress}"}), 404

    success = cams_client.deleteAgentMapping(aiAgentAddress)
    if success:
        return '', 204  # No content
    else:
        # This might indicate a race condition or an issue with the CAMS client's delete logic
        # if getAgentMapping found it but delete failed.
        return jsonify({"error": f"Failed to delete agent mapping for {aiAgentAddress}. It might have been deleted already or an internal error occurred."}), 500

# Initialize metrics collector
metrics = MetricsCollector()

# Register health check routes with metrics
register_health_check_routes(app, cams_client, metrics)

if __name__ == '__main__':
    # This is for conceptual testing if one were to run this file directly.
    # In a real scenario, this would be run by a WSGI server like Gunicorn.

    # Register routes (in a real app, this would be in a separate app.py or similar)
    app.run(debug=True, host='0.0.0.0', port=5000)   # 1. Run this file: python agent_management_api.py
    # 2. Use curl or Postman to send requests, e.g.:
    #    curl -X POST -H "Content-Type: application/json" -d '{"aiAgentAddress":"test@example.com", "inboxDestinationType":"GCP_PUBSUB_TOPIC", "inboxName":"test-topic"}' http://127.0.0.1:5000/v1/agent-inboxes
    #    curl http://127.0.0.1:5000/v1/agent-inboxes/test@example.com
    #    curl -X PUT -H "Content-Type: application/json" -d '{"status":"INACTIVE"}' http://127.0.0.1:5000/v1/agent-inboxes/test@example.com
    #    curl -X DELETE http://127.0.0.1:5000/v1/agent-inboxes/test@example.com

    # app.run(debug=True) # Do not run Flask app directly in production environment
    print("agent_management_api.py created conceptually. Not running Flask server.")
    print("Review the code for API endpoint handlers and CAMS client integration.")

# Placeholder for AGENTS.md checks - none specified for this task directly for this file.
# However, general coding standards and error handling are followed.

# End of services/router/agent_management_api.py
