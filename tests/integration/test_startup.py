from fastapi.testclient import TestClient

from src.api.config import get_settings
from src.api.main import app


def test_app_starts_in_demo_mode_when_azure_settings_missing(monkeypatch):
    # No Azure OpenAI credentials must never crash startup -- `docker run`
    # with zero configuration has to work, falling back to demo mode.
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    get_settings.cache_clear()

    try:
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["demo_mode"] is True
    finally:
        get_settings.cache_clear()


def test_app_starts_normally_when_azure_settings_present(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    get_settings.cache_clear()

    try:
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["demo_mode"] is False
    finally:
        get_settings.cache_clear()
