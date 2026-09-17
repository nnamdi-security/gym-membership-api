from sqlmodel import create_engine, Session
from app.core.config import settings


engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)


def get_db():
    with Session(engine) as session:
        yield session
