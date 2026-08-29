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


def make_fake_analysis(summary: str) -> AnalysisResult:
    return AnalysisResult(detected_context="work", plain_explanation="explanation", summary=summary, red_flags=[])


def test_analyze_batch_returns_a_result_per_file():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = [
        (make_fake_analysis("First file summary."), b"%PDF-1.4 first"),
        (make_fake_analysis("Second file summary."), b"%PDF-1.4 second"),
    ]
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/batch",
        files=[
            ("files", ("a.txt", b"First file", "text/plain")),
            ("files", ("b.txt", b"Second file", "text/plain")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    assert body["results"][0]["filename"] == "a.txt"
    assert body["results"][0]["status"] == "ok"
    assert body["results"][0]["analysis"]["summary"] == "First file summary."
    assert body["results"][1]["filename"] == "b.txt"


def test_analyze_batch_continues_after_one_file_fails():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = [
        (make_fake_analysis("Good file."), b"%PDF-1.4 good"),
        ExtractionError("corrupt file"),
    ]
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/batch",
        files=[
            ("files", ("good.txt", b"Good content", "text/plain")),
            ("files", ("bad.pdf", b"not a real pdf", "application/pdf")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["status"] == "ok"
    assert body["results"][1]["status"] == "error"
    assert body["results"][1]["status_code"] == 422


def test_analyze_batch_reports_415_and_502_per_file():
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.side_effect = [
        UnsupportedFileTypeError("no extractor for .png"),
        AnalysisError("llm failed"),
    ]
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze/batch",
        files=[
            ("files", ("photo.png", b"fake", "image/png")),
            ("files", ("note.txt", b"hello", "text/plain")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["status_code"] == 415
    assert body["results"][1]["status_code"] == 502


def test_analyze_batch_rejects_too_many_files(monkeypatch):
    monkeypatch.setenv("MAX_BATCH_FILES", "1")
    from src.api.config import get_settings

    get_settings.cache_clear()

    try:
        response = client.post(
            "/analyze/batch",
            files=[
                ("files", ("a.txt", b"a", "text/plain")),
                ("files", ("b.txt", b"b", "text/plain")),
            ],
        )
        assert response.status_code == 413
    finally:
        get_settings.cache_clear()
