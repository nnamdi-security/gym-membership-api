from sqlmodel import create_engine, Session
from app.core.config import settings


engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)


def get_database():
    with Session(engine) as session:
        yield session
