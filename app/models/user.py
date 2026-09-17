from datetime import datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, String
from sqlmodel import Field, SQLModel

from app.models.base import utc_now


class UserRole(StrEnum):
    MEMBER = "member"
    FRONT_DESK = "front_desk"
    ADMIN = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)

    email: str = Field(sa_column=Column(String(255), nullable=False, unique=True, index=True,))

    password_hash: str = Field(sa_column=Column(String(255), nullable=False))

    role: UserRole = Field(default=UserRole.MEMBER, nullable=False)

    created_at: datetime = Field(efault_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))

    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))