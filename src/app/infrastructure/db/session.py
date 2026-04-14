from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from app.config.settings import get_settings

class Base(DeclarativeBase):
    pass

_engine: Engine | None = None
_session_factory = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        settings = get_settings()
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not configured.")

        _engine = create_engine(
            settings.database_url,
            echo=False,
            future=True,
        )

    return _engine


def SessionLocal() -> Session:
    return _session_factory(bind=get_engine())
