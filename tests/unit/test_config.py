import pytest

from src.api.config import Settings


def test_rate_limit_per_minute_defaults_when_env_var_absent(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)

    settings = Settings()

    assert settings.rate_limit_per_minute == 20


def test_rate_limit_per_minute_uses_env_var_when_set(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "5")

    settings = Settings()

    assert settings.rate_limit_per_minute == 5


def test_max_file_size_bytes_defaults_when_env_var_is_empty_string(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_BYTES", "")

    settings = Settings()

    assert settings.max_file_size_bytes == 10 * 1024 * 1024


def test_max_file_size_bytes_uses_env_var_when_set(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_BYTES", "2048")

    settings = Settings()

    assert settings.max_file_size_bytes == 2048


def test_validate_raises_when_azure_openai_endpoint_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")

    settings = Settings()

    with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT"):
        settings.validate()


def test_validate_raises_when_azure_openai_api_key_missing(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")

    settings = Settings()

    with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY"):
        settings.validate()


def test_validate_passes_when_required_settings_present(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "some-key")

    settings = Settings()

    settings.validate()  # should not raise
