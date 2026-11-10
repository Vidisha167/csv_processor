import os

# Defaults so tests also run outside Docker (e.g. on GitHub Actions).
# Inside your containers, the values from .env win.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://app:app_password@localhost:5432/csvjobs")
os.environ.setdefault("MINIO_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin123")
os.environ.setdefault("MINIO_BUCKET", "csv-uploads")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    """Test client whose DB changes are rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint", autoflush=False
    )

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)  # not used as a context manager, so startup (MinIO) is skipped
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()