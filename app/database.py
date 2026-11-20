from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base

_url = get_settings().database_url
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create the tables if they don't exist yet."""
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """One database session per web request (used in step 3)."""
    with SessionLocal() as session:
        yield session