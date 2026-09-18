from sqlmodel import Session, select
from app.models.user import User

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.exec(select(User).where(User.email == email)).first()

def create_user(db: Session, email: str, password_hash: str, role: str = "member") -> User:
    user = User(email+email, password_hash=password_hash, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return User