Windsurf Task 07: Prepare for Containerization & Basic Kubernetes Deployment
1. Task Objective
This task is to prepare the Message Router Service for deployment to Google Kubernetes Engine (GKE) by creating necessary containerization artifacts and basic Kubernetes manifest files. This will provide the foundation for DevOps teams to build upon for full-scale deployments.

This task is a critical bridge between our application code development and operational deployment.

2. Context & Rationale
While full GKE deployment involves complex CI/CD and infrastructure management, creating a Dockerfile and basic Kubernetes YAMLs allows us to:

Package the application: Define how our Python services are built into container images.
Define deployment intent: Specify the desired state for our application within a Kubernetes cluster.
Facilitate local testing: Enable developers to run the application in a containerized environment similar to production.
Streamline handover: Provide clear artifacts for a DevOps team to take over the deployment process.
3. Detailed Requirements
Windsurf should focus on the main application components that will be deployed as services: the Message Router Service (which includes the Agent Management APIs and integrates with CAMS).

3.1. Dockerfile for the Message Router Service
Create a Dockerfile that builds a production-ready Docker image for the Message Router Service.

Location: services/router/Dockerfile
Base Image: Use a suitable Python base image (e.g., python:3.9-slim-buster or a similar lightweight official image).
Dependencies: Install all necessary Python dependencies (from requirements.txt). Assume a requirements.txt file will be present in services/router/ that lists all the Python libraries required for the router and its internal CAMS client.
Application Code: Copy the relevant application code (all of services/router/ and services/cams/ and any common utilities needed) into the container.
Entrypoint: Define the CMD or ENTRYPOINT to run the main application process (e.g., assuming a main.py or an equivalent entry point for the router).
Port Exposure: Expose the port on which the API listens (e.g., 8080).
Best Practices: Follow Docker best practices (e.g., multi-stage builds for smaller images if applicable, non-root user, proper caching layers).
3.2. Basic Kubernetes Manifests
Create basic Kubernetes YAML files for deploying the Message Router Service. These should define the minimum necessary resources.

Deployment (e.g., router-deployment.yaml):
Deployment: Define a Deployment resource.
Replica Count: Start with a sensible default (e.g., 2 or 3 replicas for high availability).
Container Image: Reference the Docker image that will be built from the Dockerfile.
Resource Requests/Limits: Include basic CPU and memory requests and limits for the container (e.g., cpu: "250m", memory: "512Mi").
Environment Variables: Show how basic environment variables (e.g., for GCP Project ID, database host if not integrated via service discovery) would be passed. Do not include secrets directly; indicate placeholders for Secret references if needed later.
Service (e.g., router-service.yaml):
Service: Define a Service resource (ClusterIP for internal access, or LoadBalancer for external exposure via API Gateway if implied). Given the API Gateway is upstream, a ClusterIP or NodePort service behind an Ingress (managed by API Gateway) is likely. For simplicity, start with ClusterIP.
Port Mapping: Map the service port to the container port.
3.3. Configuration Management Strategy
Briefly document how configuration specific to environments (e.g., database connection strings, Pub/Sub project IDs) should be managed when deploying to Kubernetes.

Suggest using Kubernetes Secrets for sensitive information (e.g., database passwords) and ConfigMaps for non-sensitive configuration.
Show how these would be referenced as environment variables in the Deployment YAML.
4. Dependencies
Completed application code for the Router Service (services/router/) and CAMS (services/cams/) from previous tasks.
Knowledge of the required Python dependencies (assume a requirements.txt will be created).
5. Expected Output from Windsurf
Upon completion, Windsurf should provide:

services/router/Dockerfile: The Dockerfile for the Message Router Service.
deployment/kubernetes/router-deployment.yaml: Basic Kubernetes Deployment manifest.
deployment/kubernetes/router-service.yaml: Basic Kubernetes Service manifest.
deployment/kubernetes/README.md: A README file explaining:
How to build the Docker image.
How to apply the Kubernetes manifests (conceptual kubectl apply -f).
The strategy for managing environment-specific configuration and secrets.
6. Output Location
The Dockerfile should be placed directly in services/router/.
The Kubernetes YAML files and their README.md should be placed in a new directory: deployment/kubernetes/.