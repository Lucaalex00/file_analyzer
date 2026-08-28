import pytest
from fastapi.testclient import TestClient

from src.api.config import get_settings
from src.api.main import app


def test_app_startup_fails_fast_when_azure_settings_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    get_settings.cache_clear()

    try:
        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT"):
            with TestClient(app):
                pass
    finally:
        get_settings.cache_clear()


def test_app_startup_succeeds_when_azure_settings_present(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    get_settings.cache_clear()

    try:
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
    finally:
        get_settings.cache_clear()
