import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:17") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def test_engine(postgres_container):
    raw_url = postgres_container.get_connection_url()

    if raw_url.startswith("postgresql+psycopg2://"):
        raw_url = raw_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

    engine = create_engine(raw_url, echo=False)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def migrated_engine(test_engine):
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        test_engine.url.render_as_string(hide_password=False),
    )

    command.upgrade(alembic_cfg, "head")

    yield test_engine

@pytest.fixture(scope="function")
def db_session(migrated_engine):
    connection = migrated_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
