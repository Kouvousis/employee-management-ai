from sqlalchemy.orm import selectinload
from sqlmodel import Session, select
from database import engine
from models import Employee
from rag.vectorstores.employee_store import COLLECTION_NAME, CONNECTION_STRING, _build_document
from langchain_postgres import PGVector
from rag.config import EMBEDDINGS


def delete_employee_vector(employee_id: int) -> None:
    """Remove the vector document for an employee that has been hard-deleted from the DB."""
    store = PGVector(
        embeddings=EMBEDDINGS,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )
    store.delete(filter={"employee_id": employee_id})


def sync_single_employee(employee_id: int) -> None:
    """Delete and rebuild the vector document for one employee after a write operation."""
    store = PGVector(
        embeddings=EMBEDDINGS,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )

    with Session(engine) as session:
        employee = session.exec(
            select(Employee)
            .where(Employee.id == employee_id)
            .options(selectinload(Employee.tasks))
        ).one()
        doc = _build_document(employee)

    store.delete(filter={"employee_id": employee_id})
    store.add_documents([doc])
