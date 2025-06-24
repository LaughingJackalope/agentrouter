# Async Migration Guide

This document outlines the changes made to migrate the Message Router Service to an async-native architecture using FastAPI and ASGI.

## Key Changes

### 1. Framework Migration
- Replaced Flask with FastAPI for native async support
- Added Uvicorn as the ASGI server
- Updated Dockerfile to use Uvicorn instead of Gunicorn

### 2. Async Dependencies
- Added `fastapi`, `uvicorn[standard]`, and `pydantic` for the web framework
- Added `httpx` for async HTTP client
- Added `asyncpg` for async PostgreSQL support
- Added `sqlalchemy[asyncio]` for async ORM support
- Added `pytest-asyncio` for async testing

### 3. Code Structure
- Created a modular router structure under `routers/`
- Implemented dependency injection for services
- Added proper error handling and logging
- Implemented health check endpoints

### 4. API Changes
- All endpoints are now async
- Request/response models use Pydantic for validation
- Improved error handling and status codes
- Added OpenAPI documentation

## Running the Service

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables (create a `.env` file):
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
   CAMS_API_URL=http://localhost:8001
   ```

3. Run the service:
   ```bash
   uvicorn main:app --reload
   ```

### Production

Use the provided Dockerfile:

```bash
docker build -t message-router .
docker run -p 8080:8080 message-router
```

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

## Deployment

The service is designed to be deployed in Kubernetes. Update the `router-deployment.yaml` to use the new Docker image and environment variables.

## Monitoring

Health check endpoints:
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

## Performance Considerations

- The service is now fully async, allowing for better concurrency
- Database connections are managed with connection pooling
- Request timeouts and retries are configurable

## Next Steps

- [ ] Add rate limiting
- [ ] Implement circuit breakers for external services
- [ ] Add distributed tracing
- [ ] Set up monitoring dashboards
