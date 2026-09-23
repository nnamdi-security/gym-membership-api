from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.api.dependencies.jobs import verify_daily_job_api_key
from app.db.session import get_session
from app.repositories.job_run_repository import JobRunRepository
from app.repositories.membership_repository import MembershipRepository
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.job import DailyJobResponse
from app.services.daily_job_service import DailyJobService

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


SESSION_DEPENDENCY = Depends(get_session)

JOB_API_KEY_DEPENDENCY = Depends(verify_daily_job_api_key)


def get_daily_job_service(
    session: Session = SESSION_DEPENDENCY,
) -> DailyJobService:
    return DailyJobService(
        session=session,
        job_run_repository=JobRunRepository(session),
        membership_repository=MembershipRepository(session),
        reminder_repository=ReminderRepository(session),
    )


DAILY_JOB_SERVICE_DEPENDENCY = Depends(get_daily_job_service)


# Daily job endpoint
@router.post(
    "/daily",
    response_model=DailyJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Run daily membership maintenance",
    description=(
        "Expire overdue memberships and create seven-day "
        "renewal reminders. Safe to trigger more than once "
        "for the same date."
    ),
    dependencies=[JOB_API_KEY_DEPENDENCY],
)
def run_daily_job(
    service: DailyJobService = DAILY_JOB_SERVICE_DEPENDENCY,
):
    result = service.run()

    return DailyJobResponse(
        status=result.status,
        expired_memberships=result.expired_memberships,
        reminders_created=result.reminders_created,
    )
