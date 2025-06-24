-- SQL DDL for the agent_inboxes table (PostgreSQL compatible)

CREATE TABLE agent_inboxes (
    aiAgentAddress VARCHAR(255) PRIMARY KEY NOT NULL,
    inboxDestinationType VARCHAR(50) NOT NULL DEFAULT 'GCP_PUBSUB_TOPIC',
    inboxName VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    lastHealthCheckTimestamp TIMESTAMP WITH TIME ZONE,
    registrationTimestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lastUpdatedTimestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedBy VARCHAR(255),
    description TEXT,
    ownerTeam VARCHAR(255)
);

-- Trigger function to update lastUpdatedTimestamp on any row update
CREATE OR REPLACE FUNCTION update_last_updated_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.lastUpdatedTimestamp = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to execute the function before any update on the agent_inboxes table
CREATE TRIGGER update_agent_inboxes_last_updated
BEFORE UPDATE ON agent_inboxes
FOR EACH ROW
EXECUTE FUNCTION update_last_updated_timestamp_column();

COMMENT ON TABLE agent_inboxes IS 'Stores mapping of AI Agent Addresses to their inbox destinations and status.';
COMMENT ON COLUMN agent_inboxes.aiAgentAddress IS 'Unique identifier for an AI Agent.';
COMMENT ON COLUMN agent_inboxes.inboxDestinationType IS 'Type of destination, e.g., GCP_PUBSUB_TOPIC.';
COMMENT ON COLUMN agent_inboxes.inboxName IS 'Actual name of the Pub/Sub topic or other inbox.';
COMMENT ON COLUMN agent_inboxes.status IS 'Operational status of the AI Agent (ACTIVE or INACTIVE).';
COMMENT ON COLUMN agent_inboxes.lastHealthCheckTimestamp IS 'Timestamp of the last successful health check (UTC).';
COMMENT ON COLUMN agent_inboxes.registrationTimestamp IS 'Timestamp of when the agent mapping was first registered (UTC).';
COMMENT ON COLUMN agent_inboxes.lastUpdatedTimestamp IS 'Timestamp of the last update to this record (UTC).';
COMMENT ON COLUMN agent_inboxes.updatedBy IS 'Entity (user or service) that last updated the record.';
COMMENT ON COLUMN agent_inboxes.description IS 'Human-readable description of the agent.';
COMMENT ON COLUMN agent_inboxes.ownerTeam IS 'Team responsible for managing this AI Agent.';
