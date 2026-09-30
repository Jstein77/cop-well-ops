import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

READER = {"X-Forwarded-Email": "reader@example.com", "X-Forwarded-Groups": "wellops.reader"}
NO_ROLES = {"X-Forwarded-Email": "nobody@example.com"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WELL_OPS_ENV", "test")
    monkeypatch.setenv("WELL_OPS_DB_PATH", str(tmp_path / "wells.db"))
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()
