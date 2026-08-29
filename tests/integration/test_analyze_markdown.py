from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.analyzer.document_analyzer import AnalysisError
from src.analyzer.schemas import AnalysisResult
from src.api.dependencies import get_pipeline
from src.api.main import app
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError

client = TestClient(app)


def override_pipeline(fake_pipeline):
    app.dependency_overrides[get_pipeline] = lambda: fake_pipeline


def teardown_function():
    app.dependency_overrides.clear()


def make_fake_analysis():
    return AnalysisResult(
        detected_context="legal",
        plain_explanation="This is a rental agreement.",
        summary="A one-year lease.",
        red_flags=[],
    )


def test_analyze_markdown_returns_markdown_with_download_filename():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.return_value = (make_fake_analysis(), b"%PDF-1.4 unused")
    fake_pipeline.render_markdown.return_value = "# Analysis report\n\nA one-year lease."
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/markdown",
        files={"file": ("lease.txt", b"Some lease text", "text/plain")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.headers["content-disposition"] == 'attachment; filename="lease-report.md"'
    assert response.text == "# Analysis report\n\nA one-year lease."


def test_analyze_markdown_returns_415_for_unsupported_file_type():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = UnsupportedFileTypeError("no extractor for .png")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/markdown",
        files={"file": ("photo.png", b"fake image bytes", "image/png")},
    )

    assert response.status_code == 415


def test_analyze_markdown_returns_422_on_extraction_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = ExtractionError("corrupt file")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/markdown",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 422


def test_analyze_markdown_returns_502_on_analysis_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = AnalysisError("llm failed")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/markdown",
        files={"file": ("note.txt", b"Hello world", "text/plain")},
    )

    assert response.status_code == 502
