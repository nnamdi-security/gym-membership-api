from datetime import date, timedelta

from app.models.membership import Membership, MembershipStatus
from app.models.reminder import ReminderKind
from app.services.daily_job_service import (
    DAILY_JOB_NAME,
    DailyJobService,
)

class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0

    def flush(self):
        self.flushes += 1

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1
