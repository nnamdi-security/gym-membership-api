from sqlalchemy import text
from sqlmodel import Session, create_engine

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # SQLAlchemy checks that a pooled connection is alive before handing it to your code.
)


def get_session():
    with Session(engine) as session:
        yield session


def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True
