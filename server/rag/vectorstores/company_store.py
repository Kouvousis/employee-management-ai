import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, text
from rag.config import EMBEDDINGS

load_dotenv()

COMPANY_DOCS = Path(__file__).parent.parent.parent / "company_docs"
COLLECTION_NAME = "company_knowledge"
CONNECTION_STRING = os.getenv("DATABASE_URL", "")


def _is_indexed() -> bool:
    """Return True if the company_knowledge collection already has embeddings."""
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


def get_company_store() -> PGVector:
    """Return the PGVector store, indexing company docs on first call."""
    store = PGVector(
        embeddings=EMBEDDINGS,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )

    if _is_indexed():
        return store

    loader = DirectoryLoader(
        str(COMPANY_DOCS),
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    store.add_documents(chunks)
    return store
