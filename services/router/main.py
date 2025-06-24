"""
Main FastAPI application for the Message Router Service.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import uvicorn
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global application state
class AppState:
    def __init__(self):
        self.metrics = {}
        self.startup_time = None

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    app.state.app_state = AppState()
    app.state.app_state.startup_time = "2025-06-24T00:00:00Z"  # Should be datetime.utcnow().isoformat() in production
    logger.info("Starting up application...")
    
    # Initialize resources (database connections, etc.)
    try:
        # Initialize database connection pool here
        logger.info("Application startup complete")
        yield
    finally:
        # Cleanup resources
        logger.info("Shutting down application...")
        # Close database connections here
        logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Message Router Service",
    description="Async-native message routing service for AI agent communication",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return {"status": "healthy"}

# Import and include routers
from .routers import messages, health, agent_health, agent_management

app.include_router(messages.router, prefix="/v1/messages", tags=["messages"])
app.include_router(agent_management.router, tags=["agent-management"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(agent_health.router, prefix="/v1", tags=["agent-health"])

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint that provides API information."""
    return {
        "name": "Message Router Service",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

# For local development
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=True,
        workers=1,
    )
