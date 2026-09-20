from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend API for FitPro Gym Membership & Classes."
)



app.include_router(api_router, prefix="/api/v1")
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs"
    }