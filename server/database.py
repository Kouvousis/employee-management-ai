import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(
    url=DATABASE_URL,
    echo=os.getenv("DEVELOPMENT_MODE", "false").lower() == "true",
)


def create_db_and_tables():
    """Create all tables defined in SQLModel metadata. Safe to call on every startup — skips tables that already exist."""
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Error creating database and tables: {e}")
        raise


def get_session():
    """FastAPI dependency that yields a per-request Session.
    Rolls back automatically on any SQLAlchemy error so the connection is never left in a broken state."""
    with Session(engine) as session:
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Session error: {e}")
            raise
