from openai import AzureOpenAI, OpenAI

from src.analyzer.demo_client import DemoAIClient
from src.api import dependencies
from src.api.config import get_settings


def _reset_caches():
    get_settings.cache_clear()
    dependencies.get_document_analyzer.cache_clear()
    dependencies.get_document_comparator.cache_clear()


def test_uses_demo_client_when_no_provider_configured(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    _reset_caches()

    try:
        analyzer = dependencies.get_document_analyzer()
        assert isinstance(analyzer._client, DemoAIClient)
        assert analyzer._deployment == "demo"
    finally:
        _reset_caches()


def test_uses_real_azure_client_when_azure_settings_present(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    _reset_caches()

    try:
        analyzer = dependencies.get_document_analyzer()
        assert isinstance(analyzer._client, AzureOpenAI)
        assert analyzer._deployment == "gpt-4o-mini"
    finally:
        _reset_caches()


def test_uses_groq_client_when_only_groq_configured(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "some-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    _reset_caches()

    try:
        analyzer = dependencies.get_document_analyzer()
        # Groq is OpenAI-API-compatible, so it's the plain OpenAI client
        # (not AzureOpenAI) pointed at Groq's base URL.
        assert isinstance(analyzer._client, OpenAI)
        assert not isinstance(analyzer._client, AzureOpenAI)
        assert str(analyzer._client.base_url) == "https://api.groq.com/openai/v1/"
        assert analyzer._deployment == "openai/gpt-oss-20b"
    finally:
        _reset_caches()


def test_azure_takes_priority_over_groq_when_both_configured(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    monkeypatch.setenv("GROQ_API_KEY", "some-groq-key")
    _reset_caches()

    try:
        analyzer = dependencies.get_document_analyzer()
        assert isinstance(analyzer._client, AzureOpenAI)
    finally:
        _reset_caches()


def test_comparator_also_uses_the_same_provider_selection(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "some-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    _reset_caches()

    try:
        comparator = dependencies.get_document_comparator()
        assert isinstance(comparator._client, OpenAI)
        assert comparator._deployment == "openai/gpt-oss-20b"
    finally:
        _reset_caches()
