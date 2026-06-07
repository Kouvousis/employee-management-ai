import os
from logging.config import fileConfig
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
from alembic import context

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read DATABASE_URL from .env instead of alembic.ini
# configparser treats % as interpolation — escape it so %40 (encoded @) passes through
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"].replace("%", "%%"))

# Import all models so they register their tables with SQLModel.metadata
import models  # noqa: F401

target_metadata = SQLModel.metadata

EXCLUDE_TABLES = {"langchain_pg_collection", "langchain_pg_embedding"}


def include_object(object, name, type_, reflected, compare_to):
    """Exclude tables managed by langchain-postgres from autogenerate."""
    if type_ == "table" and name in EXCLUDE_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()