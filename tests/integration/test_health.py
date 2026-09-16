from fastapi.testclient import TestClient

from src.api.config import get_settings
from src.api.dependencies import get_ai_budget
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


def test_health_reports_demo_mode_once_the_hourly_ai_budget_is_spent(monkeypatch):
    # A configured provider whose budget is gone serves simulated answers, so
    # the UI must show the same banner as an unconfigured one.
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    monkeypatch.setenv("AI_HOURLY_BUDGET", "1")
    get_settings.cache_clear()
    get_ai_budget.cache_clear()

    try:
        assert client.get("/health").json()["demo_mode"] is False

        get_ai_budget().try_consume()

        body = client.get("/health").json()
        assert body["demo_mode"] is True
        assert body["ai_provider"] == "demo"
    finally:
        get_settings.cache_clear()
        get_ai_budget.cache_clear()
