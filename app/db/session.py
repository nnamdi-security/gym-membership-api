from sqlmodel import create_engine, Session
from app.core.config import Settings

from sqlalchemy import text

engine = create_engine(
    Settings.database_url,
    echo=Settings.debug,
    pool_pre_ping=True, #SQLAlchemy checks that a pooled connection is alive before handing it to your code.
)

def get_database():
    with Session(engine) as session:
        yield session


def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return True