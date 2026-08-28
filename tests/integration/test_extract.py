from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.api.dependencies import get_extractor_factory
from src.api.main import app
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError

client = TestClient(app)


def override_factory(fake_factory):
    app.dependency_overrides[get_extractor_factory] = lambda: fake_factory


def teardown_function():
    app.dependency_overrides.clear()


def test_extract_returns_real_text_for_txt_file():
    # No override: exercises the real ExtractorFactory/TextExtractor, no LLM involved.
    response = client.post(
        "/extract",
        files={"file": ("note.txt", b"Hello, this is a contract.", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "Hello, this is a contract."}


def test_extract_returns_413_when_file_too_large(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_BYTES", "10")
    from src.api.config import get_settings

    get_settings.cache_clear()

    response = client.post(
        "/extract",
        files={"file": ("note.txt", b"this is definitely more than ten bytes", "text/plain")},
    )

    assert response.status_code == 413
    get_settings.cache_clear()


def test_extract_returns_415_for_unsupported_file_type():
    fake_factory = MagicMock()
    fake_factory.get_extractor.side_effect = UnsupportedFileTypeError("no extractor for .png")
    override_factory(fake_factory)

    response = client.post(
        "/extract",
        files={"file": ("photo.png", b"fake image bytes", "image/png")},
    )

    assert response.status_code == 415


def test_extract_returns_422_on_extraction_error():
    fake_extractor = MagicMock()
    fake_extractor.extract.side_effect = ExtractionError("corrupt file")
    fake_factory = MagicMock()
    fake_factory.get_extractor.return_value = fake_extractor
    override_factory(fake_factory)

    response = client.post(
        "/extract",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 422
