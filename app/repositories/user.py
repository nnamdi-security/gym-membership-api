from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)

        return self.session.exec(statement).first()

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def create(self, user: User) -> User:
        self.session.add(user)

        try:
            self.session.commit()
        except IntegrityError:       #Make the repository recover its transaction
            self.session.rollback()
            raise

        self.session.refresh(user)

        return user