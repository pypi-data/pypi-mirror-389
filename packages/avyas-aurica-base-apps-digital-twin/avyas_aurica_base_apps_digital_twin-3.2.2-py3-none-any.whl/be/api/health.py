"""
Health Check Endpoint

Simple health check to verify the Digital Twin is active.
"""

from fastapi import APIRouter
from datetime import datetime
import os

# Import auth decorator
try:
    from src.aurica_auth import public
except ImportError:
    def public(func):
        return func

router = APIRouter()


@router.get("/")
@public
async def health_check():
    """
    Health check endpoint.
    Registered at: /digital-twin/api/health/
    Public endpoint - no authentication required.
    """
    return {
        "status": "healthy",
        "service": "digital-twin",
        "version": "1.0.0",
        "dt_active": True,
        "timestamp": datetime.utcnow().isoformat(),
        "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
        "model": os.getenv("LLM_MODEL", "gpt-4"),
        "dt_mode": os.getenv("DT_MODE", "autonomous"),
        "message": "Digital Twin Agent is operational"
    }
