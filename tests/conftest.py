import os
from pathlib import Path

# Test settings. These must be set before the app is imported.
TEST_DB = Path(__file__).parent / "test.db"
os.environ.update(
    {
        "ANTHROPIC_API_KEY": "test-key",
        "TMDB_API_KEY": "test-key",
        "OMDB_API_KEY": "test-key",
        "ACCESS_CODES": "alice:code-alice,bob:code-bob",
        "DATABASE_URL": f"sqlite:///{TEST_DB.as_posix()}",
    }
)

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, engine
from app.main import app
from app.models import Base
from app.services.catalog import CatalogEntry


@pytest.fixture(autouse=True)
def fresh_db():
    """Start every test with empty tables."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def session():
    with SessionLocal() as s:
        yield s


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_entry():
    def _make(key="tv-1", title="Dark"):
        return CatalogEntry(
            key=key,
            title=title,
            year="2017",
            type="TV Series",
            genres=["Drama"],
            imdb_rating="8.7",
            streaming=["Netflix"],
        )

    return _make