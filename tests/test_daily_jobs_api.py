from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def job_headers() -> dict[str, str]:
    return {
        "X-API-Key": settings.daily_job_api_key,
    }



def test_daily_job_rejects_missing_api_key():
    response = client.post(
        "/api/v1/jobs/daily"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid job API key"
    }



def test_daily_job_rejects_wrong_api_key():
    response = client.post(
        "/api/v1/jobs/daily",
        headers={
            "X-API-Key": "wrong-key",
        },
    )

    assert response.status_code == 401



def test_daily_job_accepts_valid_api_key():
    response = client.post(
        "/api/v1/jobs/daily",
        headers=job_headers(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] in {
        "completed",
        "already_run",
    }



def test_daily_job_endpoint_is_idempotent():
    first = client.post(
        "/api/v1/jobs/daily",
        headers=job_headers(),
    )

    second = client.post(
        "/api/v1/jobs/daily",
        headers=job_headers(),
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert second.json()["status"] == "already_run"



    assert first.json()["status"] == "completed"
    assert second.json()["status"] == "already_run"