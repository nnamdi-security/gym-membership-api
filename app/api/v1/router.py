from fastapi import APIRouter, HTTPException, status

from app.api.v1.auth import router as auth_router
from app.api.v1.membership import router as memberships_router
from app.api.v1.plans import router as plans_router
from app.api.v1.webhooks import router as webhooks_router
from app.db.session import check_database_connection
from app.api.v1.payments import router as payments_router
from app.api.v1.classes import router as classes_router
from app.api.v1.checkins import router as checkins_router
from app.api.v1.jobs import router as jobs_router

from app.core.redis import get_redis
from app.services.redis_service import RedisService

from app.api.v1.live import router as live_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(memberships_router)
api_router.include_router(plans_router)
api_router.include_router(webhooks_router)
api_router.include_router(payments_router)
api_router.include_router(classes_router)
api_router.include_router(checkins_router)
api_router.include_router(jobs_router)
api_router.include_router(live_router)

@api_router.get("/health", tags=["System"], summary="Check API health")
def health_check():
    return {"status": "ok", "service": "fitpro-api"}


# Temporary database health endpoint
@api_router.get(
    "/health/database",
    tags=["System"],
    summary="Check database connectivity",
)
def database_health_check():
    try:
        check_database_connection()
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )

    return {
        "status": "ok",
        "database": "postgresql",
    }




@api_router.get(
    "/health/redis",
    tags=["System"],
    summary="Check Redis connectivity",
)
def redis_health_check():
    try:
        service = RedisService(
            get_redis()
        )

        service.ping()

    except Exception: # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is unavailable",
        ) from None

    return {
        "status": "ok",
        "redis": "available",
    }