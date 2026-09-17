from fastapi import APIRouter, HTTPException, status
from app.db.session import check_database_connection

api_router = APIRouter()


@api_router.get(
    "/health",
    tags=["System"],
    summary="Check API health"
)
def health_check():
    return {
        "status": "ok",
        "service": "fitpro-api"
    }





# Temporary database health endpoint
@api_router.get(
    "/health/database",
    tags=["System"],
    summary="Check database connectivity",
)
def database_health_check():
    try:
        check_database_connection()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )

    return {
        "status": "ok",
        "database": "postgresql",
    }