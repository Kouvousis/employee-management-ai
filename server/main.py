from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from database import create_db_and_tables, engine
from seed import seed
from rag.vectorstores.company_store import get_company_store
from rag.vectorstores.employee_store import get_employee_store
from routers.auth import router as auth_router
from routers.employees import router as employees_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, seed reference data, and both vector stores.
    Code after yield runs on shutdown.
    """
    create_db_and_tables()
    with Session(engine) as session:
        seed(session)
    get_company_store()
    get_employee_store()
    yield
    print("Exiting application")


app = FastAPI(title="NovaTech Solutions", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(employees_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
