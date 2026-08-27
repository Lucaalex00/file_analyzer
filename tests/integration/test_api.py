from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.analyzer.document_analyzer import AnalysisError
from src.api.dependencies import get_pipeline
from src.api.main import app
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError

client = TestClient(app)


def override_pipeline(fake_pipeline):
    app.dependency_overrides[get_pipeline] = lambda: fake_pipeline


def teardown_function():
    app.dependency_overrides.clear()


def test_analyze_returns_pdf_on_success():
    fake_pipeline = MagicMock()
    fake_pipeline.run.return_value = b"%PDF-1.4 fake pdf content"
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("note.txt", b"Hello world", "text/plain")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 fake pdf content"


def test_analyze_returns_413_when_file_too_large(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_BYTES", "10")
    from src.api.config import get_settings
    get_settings.cache_clear()

    fake_pipeline = MagicMock()
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("note.txt", b"this is definitely more than ten bytes", "text/plain")},
    )

    assert response.status_code == 413
    get_settings.cache_clear()


def test_analyze_returns_415_for_unsupported_file_type():
    fake_pipeline = MagicMock()
    fake_pipeline.run.side_effect = UnsupportedFileTypeError("no extractor for .png")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("photo.png", b"fake image bytes", "image/png")},
    )

    assert response.status_code == 415


def test_analyze_returns_422_on_extraction_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run.side_effect = ExtractionError("corrupt file")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 422


def test_analyze_returns_502_on_analysis_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run.side_effect = AnalysisError("llm failed")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("note.txt", b"Hello world", "text/plain")},
    )

    assert response.status_code == 502
