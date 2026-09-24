from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

    model_config = ConfigDict(
        from_attributes=True,
    )
