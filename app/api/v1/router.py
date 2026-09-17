from fastapi import APIRouter

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