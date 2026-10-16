import os
import asyncio
import pytest

from types import SimpleNamespace
from fastapi.testclient import TestClient


# Set a dummy API key before importing web.app
os.environ.setdefault("OPENAI_API_KEY", "test-key")


@pytest.fixture
def client():
    from web.app import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_session():
    return SimpleNamespace(
        session_id="a" * 32,
        lock=asyncio.Lock(),
        agent=None,
        chat=None,
        last_used=0.0,
        turns=0
    )
