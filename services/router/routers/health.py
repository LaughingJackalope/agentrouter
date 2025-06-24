"""
Health check endpoints for the message router service.
"""
import logging
from fastapi import APIRouter, Depends
from typing import Dict, Any
import psutil
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Models ---
class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints."""
    status: str
    timestamp: str
    details: Dict[str, Any] = {}

# --- Services ---
class HealthService:
    """Service for health check operations."""
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform health checks and return status."""
        checks = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "process": {
                    "pid": os.getpid(),
                    "uptime_seconds": self._get_process_uptime(),
                    "memory_usage": self._get_memory_usage()
                },
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent
                },
                "dependencies": {
                    # In a real implementation, check database connections, etc.
                    "database": "ok"
                }
            }
        }
        
        # If any critical check fails, update status
        if checks["details"]["system"]["disk_usage"] > 90:
            checks["status"] = "degraded"
            checks["details"]["message"] = "High disk usage detected"
            
        return checks
    
    def _get_process_uptime(self) -> float:
        """Get the uptime of the current process in seconds."""
        try:
            return (datetime.now(timezone.utc) - datetime.fromtimestamp(psutil.Process().create_time(), timezone.utc)).total_seconds()
        except Exception as e:
            logger.warning(f"Error getting process uptime: {e}")
            return -1
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage of the current process."""
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            return {
                "rss_mb": mem_info.rss / (1024 * 1024),  # RSS in MB
                "vms_mb": mem_info.vms / (1024 * 1024),  # VMS in MB
                "percent": process.memory_percent()
            }
        except Exception as e:
            logger.warning(f"Error getting memory usage: {e}")
            return {"error": str(e)}

# Initialize service
health_service = HealthService()

# --- API Endpoints ---
@router.get(
    "",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health status of the message router service."
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the message router service.
    
    Returns a 200 status code if the service is healthy, along with system metrics.
    """
    return await health_service.check_health()

@router.get(
    "/ready",
    response_model=HealthCheckResponse,
    summary="Readiness Check",
    description="Check if the service is ready to accept requests."
)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes.
    
    Returns a 200 status code if the service is ready to accept requests.
    """
    health_data = await health_service.check_health()
    if health_data["status"] != "healthy":
        health_data["status"] = "not_ready"
    return health_data

@router.get(
    "/live",
    response_model=HealthCheckResponse,
    summary="Liveness Check",
    description="Check if the service is running."
)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes.
    
    Returns a 200 status code if the service is running.
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
