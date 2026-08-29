from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.config import get_settings
from src.api.dependencies import get_pipeline
from src.api.main import app

client = TestClient(app)


def test_analyze_returns_429_after_exceeding_the_rate_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    get_settings.cache_clear()

    fake_pipeline = MagicMock()
    fake_pipeline.run.return_value = b"%PDF-1.4 fake pdf content"
    app.dependency_overrides[get_pipeline] = lambda: fake_pipeline

    try:
        for _ in range(2):
            response = client.post("/analyze", files={"file": ("note.txt", b"hi", "text/plain")})
            assert response.status_code == 200

        response = client.post("/analyze", files={"file": ("note.txt", b"hi", "text/plain")})
        assert response.status_code == 429
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def test_extract_is_independently_rate_limited_from_analyze(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    get_settings.cache_clear()

    try:
        response = client.post("/extract", files={"file": ("note.txt", b"hello world", "text/plain")})
        assert response.status_code == 200

        response = client.post("/extract", files={"file": ("note.txt", b"hello world", "text/plain")})
        assert response.status_code == 429
    finally:
        get_settings.cache_clear()
