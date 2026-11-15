import os
import uuid

# Never connect tests to the application's database.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app


@pytest.fixture
def db_factory():
    test_url = os.getenv("TEST_DATABASE_URL")
    schema = "test_" + uuid.uuid4().hex
    if test_url:
        base_engine = create_engine(test_url)
        if base_engine.dialect.name != "postgresql":
            raise ValueError("TEST_DATABASE_URL must point to an isolated PostgreSQL test database")
        with base_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = base_engine.execution_options(schema_translate_map={None: schema})
    else:
        base_engine = engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    def override():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = override
    yield factory
    app.dependency_overrides.clear()
    if test_url:
        with base_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    base_engine.dispose()


@pytest.fixture
def client(db_factory):
    with TestClient(app, headers={"X-MusicAccess": "1"}) as client:
        yield client
