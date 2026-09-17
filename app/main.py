from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import Settings



app = FastAPI(
    title=Settings.app_name,
    version="1.0.0",
    description="Backend API for FitPro Gym Membership & Classes."
)



app.include_router(api_router, prefix="/api/v1")
def root():
    return {
        "name": Settings.app_name,
        "docs": "/docs"
    }