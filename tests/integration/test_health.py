from fastapi.testclient import TestClient

from src.api.config import get_settings
from src.api.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "demo_mode" in body


def test_health_reports_demo_mode_when_azure_settings_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    get_settings.cache_clear()

    try:
        response = client.get("/health")
        assert response.json()["demo_mode"] is True
    finally:
        get_settings.cache_clear()


def test_health_reports_no_demo_mode_when_azure_settings_present(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    get_settings.cache_clear()

    try:
        response = client.get("/health")
        assert response.json()["demo_mode"] is False
    finally:
        get_settings.cache_clear()
