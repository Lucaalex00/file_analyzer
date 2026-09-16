from openai import AzureOpenAI, OpenAI

from src.analyzer.budgeted_client import BudgetedAIClient
from src.analyzer.demo_client import DemoAIClient
from src.api import dependencies
from src.api.config import get_settings


def _reset_caches():
    get_settings.cache_clear()
    dependencies.get_document_analyzer.cache_clear()
    dependencies.get_document_comparator.cache_clear()
    dependencies.get_ai_budget.cache_clear()


def _provider_client(analyzer):
    """The client actually talking to a provider.

    Paid providers are wrapped in the hourly-budget guard; the demo client
    isn't wrapped, since it costs nothing to call.
    """
    return getattr(analyzer._client, "real_client", analyzer._client)


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
        assert isinstance(_provider_client(analyzer), AzureOpenAI)
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
        assert isinstance(_provider_client(analyzer), OpenAI)
        assert not isinstance(_provider_client(analyzer), AzureOpenAI)
        assert str(_provider_client(analyzer).base_url) == "https://api.groq.com/openai/v1/"
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
        assert isinstance(_provider_client(analyzer), AzureOpenAI)
    finally:
        _reset_caches()


def test_paid_providers_are_wrapped_in_the_hourly_budget_guard(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")
    _reset_caches()

    try:
        assert isinstance(dependencies.get_document_analyzer()._client, BudgetedAIClient)
        assert isinstance(dependencies.get_document_comparator()._client, BudgetedAIClient)
    finally:
        _reset_caches()


def test_the_demo_client_is_not_budget_wrapped_since_it_costs_nothing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    _reset_caches()

    try:
        assert isinstance(dependencies.get_document_analyzer()._client, DemoAIClient)
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
        assert isinstance(_provider_client(comparator), OpenAI)
        assert comparator._deployment == "openai/gpt-oss-20b"
    finally:
        _reset_caches()
