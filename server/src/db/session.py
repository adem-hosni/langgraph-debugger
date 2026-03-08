from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core import settings

# SQLite database file will be created in your project root

# connect_args={"check_same_thread": False} is required ONLY for SQLite in FastAPI
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a database session per request
    and securely closes it when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
