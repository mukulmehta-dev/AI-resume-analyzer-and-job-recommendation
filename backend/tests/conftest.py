import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.db.session import Base, get_db
from backend.app.core.ratelimit import requests_tracker
import backend.app.routers.analyses as analyses_router

test_db_url = (os.getenv("TEST_DATABASE_URL") or "").strip()
allow_sqlite = os.getenv("ALLOW_SQLITE_TESTS", "").strip() == "1"

if not test_db_url:
    if allow_sqlite:
        test_db_url = "sqlite:///./test_runner.db"
    else:
        raise RuntimeError(
            "TEST_DATABASE_URL is unset. Set TEST_DATABASE_URL to a valid PostgreSQL connection URL "
            "or set ALLOW_SQLITE_TESTS=1 to permit local SQLite execution."
        )
elif "sqlite" in test_db_url and not allow_sqlite:
    raise RuntimeError(
        "SQLite is not permitted for TEST_DATABASE_URL unless ALLOW_SQLITE_TESTS=1 is explicitly set."
    )

connect_args = {"check_same_thread": False} if test_db_url.startswith("sqlite") else {}
engine = create_engine(test_db_url, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if test_db_url.startswith("sqlite") and os.path.exists("./test_runner.db"):
        try:
            os.remove("./test_runner.db")
        except OSError:
            pass


@pytest.fixture(autouse=True)
def clean_tables():
    Base.metadata.create_all(bind=engine)
    requests_tracker.clear()
    yield
    requests_tracker.clear()
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    original_session_local = analyses_router.SessionLocal
    analyses_router.SessionLocal = TestingSessionLocal

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()
    analyses_router.SessionLocal = original_session_local
