from pydantic import BaseModel


class DailyJobResponse(BaseModel):
    status: str
    expired_memberships: int
    reminders_created: int
