"""Shared pytest fixtures.

Sets a known API_KEY before the app imports its Settings, so auth tests are deterministic
without a real .env.
"""
import os

os.environ.setdefault("API_KEY", "test-api-key")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    return {"X-API-Key": os.environ["API_KEY"]}
