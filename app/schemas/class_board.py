from datetime import datetime

from pydantic import BaseModel


class ClassBoardResponse(BaseModel):
    class_id: int
    name: str
    starts_at: datetime
    capacity: int
    checked_in: int
    remaining: int
    full: bool