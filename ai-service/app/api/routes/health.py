"""Health check routes."""

from fastapi import APIRouter

from app.core.logger import get_logger
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    logger.info("health_check_requested")
    return HealthResponse(status="ok", service="ai-service")
