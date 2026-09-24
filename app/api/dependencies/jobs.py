import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_daily_job_api_key(
    x_api_key: str | None = Header(
        default=None,
        alias="X-API-Key",
    ),
) -> None:
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid job API key",
        )

    if not hmac.compare_digest(
        x_api_key,
        settings.daily_job_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid job API key",
        )
