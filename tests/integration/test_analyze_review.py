import base64
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.analyzer.document_analyzer import AnalysisError
from src.analyzer.schemas import AnalysisResult, RedFlag
from src.api.dependencies import get_pipeline
from src.api.main import app
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError

client = TestClient(app)


def override_pipeline(fake_pipeline):
    app.dependency_overrides[get_pipeline] = lambda: fake_pipeline


def teardown_function():
    app.dependency_overrides.clear()


def test_analyze_review_returns_analysis_and_base64_pdf():
    fake_analysis = AnalysisResult(
        detected_context="legal",
        plain_explanation="This is a rental agreement.",
        summary="A one-year lease.",
        red_flags=[
            RedFlag(
                title="Early termination penalty",
                description="Costs two months rent.",
                severity="high",
                quote="two (2) months of rent",
            )
        ],
    )
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.return_value = (fake_analysis, b"%PDF-1.4 fake pdf content")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/review",
        files={"file": ("lease.txt", b"Some lease text", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis"]["detected_context"] == "legal"
    assert body["analysis"]["red_flags"][0]["quote"] == "two (2) months of rent"
    assert base64.b64decode(body["pdf_base64"]) == b"%PDF-1.4 fake pdf content"


def test_analyze_review_returns_415_for_unsupported_file_type():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = UnsupportedFileTypeError("no extractor for .png")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/review",
        files={"file": ("photo.png", b"fake image bytes", "image/png")},
    )

    assert response.status_code == 415


def test_analyze_review_returns_422_on_extraction_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = ExtractionError("corrupt file")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/review",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 422


def test_analyze_review_returns_502_on_analysis_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = AnalysisError("llm failed")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/review",
        files={"file": ("note.txt", b"Hello world", "text/plain")},
    )

    assert response.status_code == 502
