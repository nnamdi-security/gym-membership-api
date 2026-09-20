# This ensures that before and after every test, user table is cleared
import pytest
from sqlmodel import Session, delete

from app.db.session import engine
from app.models.checkin import Checkin
from app.models.gym_class import GymClass
from app.models.job_run import JobRun
from app.models.membership import Membership
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.processed_event import ProcessedEvent
from app.models.reminder import Reminder
from app.models.user import User


def clear_database() -> None:
    with Session(engine) as session:
        # Children must be deleted before their parent rows.
        session.exec(delete(Payment))
        session.exec(delete(Reminder))
        session.exec(delete(Checkin))
        session.exec(delete(Membership))

        session.exec(delete(Plan))
        session.exec(delete(GymClass))
        session.exec(delete(User))

        session.exec(delete(JobRun))
        session.exec(delete(ProcessedEvent))

        session.commit()


@pytest.fixture(autouse=True)
def clean_database():
    clear_database()

    yield

    clear_database()


@pytest.fixture
def db_session():
    with Session(engine) as session:
        yield session
