# This makes alembic discover all models

from app.models.checkin import Checkin
from app.models.gym_class import GymClass
from app.models.job_run import JobRun
from app.models.membership import Membership
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.processed_event import ProcessedEvent
from app.models.reminder import Reminder
from app.models.user import User

__all__ = [
    "Checkin",
    "GymClass",
    "JobRun",
    "Membership",
    "Payment",
    "Plan",
    "ProcessedEvent",
    "Reminder",
    "User",
]
