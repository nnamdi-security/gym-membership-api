#This ensures that before and after every test, user table is cleared
import pytest
from sqlmodel import Session, delete

from app.db.session import engine
from app.models.user import User


@pytest.fixture(autouse=True)
def clean_users():
    with Session(engine) as session:
        session.exec(delete(User))
        session.commit()

    yield

    with Session(engine) as session:
        session.exec(delete(User))
        session.commit()

