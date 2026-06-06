import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_postgres import PGVector
from sqlalchemy import text
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from models import Employee
from database import engine
from rag.config import EMBEDDINGS

load_dotenv()

COLLECTION_NAME = "employee_data"
CONNECTION_STRING = os.getenv("DATABASE_URL", "")

if not CONNECTION_STRING:
    raise ValueError("DATABASE_URL is not set — add it to your .env file")


def _is_indexed() -> bool:
    """Return True if the employee_data collection already has embeddings."""
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


def _build_document(employee: Employee) -> Document:
    """Convert a single Employee ORM object (with tasks loaded) into a LangChain Document."""
    task_lines = "\n".join(
        f"  - {task.title} (status: {task.status.value})"
        for task in employee.tasks
    ) or "  None assigned"

    return Document(
        page_content=(
            f"Name: {employee.first_name} {employee.last_name}\n"
            f"Role: {employee.role}\n"
            f"Department: {employee.department}\n"
            f"Email: {employee.email}\n"
            f"Hire Date: {employee.hire_date}\n"
            f"Tasks:\n{task_lines}"
        ),
        metadata={"employee_id": employee.id, "source": "employee_database"},
    )


def get_employee_store() -> PGVector:
    """Return the PGVector store, indexing employee docs with task data on first call."""
    store = PGVector(
        embeddings=EMBEDDINGS,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )

    if _is_indexed():
        return store

    with Session(engine) as session:
        employees = session.exec(
            select(Employee).options(selectinload(Employee.tasks))
        ).all()
        docs = [_build_document(emp) for emp in employees]

    store.add_documents(docs)
    return store
