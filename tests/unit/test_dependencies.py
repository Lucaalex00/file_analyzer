from openai import AzureOpenAI

from src.analyzer.demo_client import DemoAIClient
from src.api import dependencies
from src.api.config import get_settings


def test_uses_demo_client_when_azure_settings_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    get_settings.cache_clear()
    dependencies.get_document_analyzer.cache_clear()

    try:
        analyzer = dependencies.get_document_analyzer()
        assert isinstance(analyzer._client, DemoAIClient)
    finally:
        get_settings.cache_clear()
        dependencies.get_document_analyzer.cache_clear()


def test_uses_real_azure_client_when_azure_settings_present(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    get_settings.cache_clear()
    dependencies.get_document_analyzer.cache_clear()

    try:
        analyzer = dependencies.get_document_analyzer()
        assert isinstance(analyzer._client, AzureOpenAI)
    finally:
        get_settings.cache_clear()
        dependencies.get_document_analyzer.cache_clear()
