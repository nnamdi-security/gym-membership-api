from fastapi import APIRouter, HTTPException, status

from app.api.v1.auth import router as auth_router
from app.api.v1.membership import router as memberships_router
from app.api.v1.plans import router as plans_router
from app.db.session import check_database_connection

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(plans_router)
api_router.include_router(memberships_router)


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
