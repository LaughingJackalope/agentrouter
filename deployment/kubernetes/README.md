# Message Router Service - Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Message Router Service to a Google Kubernetes Engine (GKE) cluster.

## Prerequisites

1. Google Cloud SDK installed and authenticated
2. Docker installed and configured to use with Google Container Registry (GCR)
3. kubectl configured to communicate with your GKE cluster
4. A GKE cluster with necessary IAM permissions

## Directory Structure

```
deployment/kubernetes/
├── README.md                 # This file
├── router-deployment.yaml    # Kubernetes Deployment for the Message Router Service
└── router-service.yaml      # Kubernetes Service for the Message Router Service
```

## Building the Docker Image

1. Navigate to the project root directory:
   ```bash
   cd /path/to/agentrouter
   ```

2. Build the Docker image:
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/message-router:latest -f services/router/Dockerfile .
   ```

3. Push the image to Google Container Registry:
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/message-router:latest
   ```

## Deploying to Kubernetes

1. Ensure you're connected to the correct Kubernetes cluster:
   ```bash
   gcloud container clusters get-credentials YOUR_CLUSTER_NAME --region YOUR_REGION
   ```

2. Create the Kubernetes ConfigMap for application configuration:
   ```bash
   kubectl create configmap app-config \
     --from-literal=gcp.project.id=YOUR_PROJECT_ID \
     --from-literal=log.level=INFO
   ```

3. Create the Kubernetes Secret for sensitive information:
   ```bash
   kubectl create secret generic database-credentials \
     --from-literal=url=postgresql://username:password@host:port/dbname
   ```

4. Deploy the application:
   ```bash
   kubectl apply -f deployment/kubernetes/
   ```

5. Verify the deployment:
   ```bash
   kubectl get pods -l app=message-router
   kubectl get svc message-router
   ```

## Configuration Management

### Environment Variables

Configuration is managed through environment variables, which can be set in the following ways:

1. **ConfigMaps**: For non-sensitive configuration
   - Managed in `router-deployment.yaml` under `env`
   - Example: `LOG_LEVEL`, `FLASK_ENV`

2. **Secrets**: For sensitive information
   - Managed in `router-deployment.yaml` under `env` with `valueFrom.secretKeyRef`
   - Example: `DATABASE_URL`

### Updating Configuration

1. Update the ConfigMap:
   ```bash
   kubectl edit configmap app-config
   ```

2. Update the Secret (if needed):
   ```bash
   kubectl edit secret database-credentials
   ```

3. Restart the pods to apply changes:
   ```bash
   kubectl rollout restart deployment message-router
   ```

## Scaling

The deployment is configured with 3 replicas by default. To scale up or down:

```bash
kubectl scale deployment message-router --replicas=5
```

## Monitoring

Basic monitoring is configured with:

- Liveness and readiness probes
- Resource requests and limits
- Prometheus metrics endpoint at `/metrics`

## Troubleshooting

### View Logs

```bash
# View logs for all pods
kubectl logs -l app=message-router --tail=50

# Stream logs
kubectl logs -f deployment/message-router
```

### Accessing the Service

For local testing, you can port-forward the service:

```bash
kubectl port-forward svc/message-router 8080:80
```

Then access the service at `http://localhost:8080`

## Cleanup

To delete the deployment:

```bash
kubectl delete -f deployment/kubernetes/
```
