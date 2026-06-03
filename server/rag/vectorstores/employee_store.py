import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from sqlalchemy import create_engine, text
from models import Employee
from sqlmodel import Session, select
from langchain_core.documents import Document
from database import engine
from rag.config import EMBEDDINGS

load_dotenv()

COLLECTION_NAME = "employee_data"
CONNECTION_STRING = os.getenv("DATABASE_URL", "")


def _is_indexed() -> bool:
    """Return True if the employee_data collection already has embeddings."""
    engine = create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        try:
            result = conn.execute(
                text(
                    "SELECT EXISTS("
                    "SELECT 1 FROM langchain_pg_embedding e "
                    "JOIN langchain_pg_collection c ON e.collection_id = c.uuid "
                    "WHERE c.name = :name)"
                ),
                {"name": COLLECTION_NAME},
            )
            return bool(result.scalar())
        except Exception:
            return False


def get_employee_store() -> PGVector:
    """Return the PGVector store, indexing employee docs on first call."""
    store = PGVector(
        embeddings=EMBEDDINGS,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )

    if _is_indexed():
        return store

    with Session(engine) as session:
        employees = session.exec(select(Employee)).all()

    docs = [Document(
        page_content=(
            f"Name: {employee.first_name} {employee.last_name}\n"
            f"Role: {employee.role}\n"
            f"Department: {employee.department}\n"
            f"Email: {employee.email}\n"
            f"Hire Date: {employee.hire_date}"
        ),
        metadata={"employee_id": employee.id, "source": "employee_database"},
    ) for employee in employees]

    store.add_documents(docs)
    return store
