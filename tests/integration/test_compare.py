from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.analyzer.comparison_schemas import ComparisonResult, Difference
from src.analyzer.document_comparator import ComparisonError
from src.api.dependencies import get_document_comparator, get_extractor_factory
from src.api.main import app
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError

client = TestClient(app)


def override_comparator(fake_comparator):
    app.dependency_overrides[get_document_comparator] = lambda: fake_comparator


def teardown_function():
    app.dependency_overrides.clear()


def test_compare_returns_the_comparison_result():
    fake_comparator = MagicMock()
    fake_comparator.compare.return_value = ComparisonResult(
        summary="Version B increases the penalty.",
        differences=[
            Difference(title="Penalty amount", description="Raised from one to two months.", change_type="modified")
        ],
    )
    override_comparator(fake_comparator)

    response = client.post(
        "/compare",
        files={
            "file_a": ("v1.txt", b"Version one text", "text/plain"),
            "file_b": ("v2.txt", b"Version two text", "text/plain"),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["comparison"]["summary"] == "Version B increases the penalty."
    assert body["comparison"]["differences"][0]["change_type"] == "modified"


def test_compare_passes_extracted_text_and_language_to_the_comparator():
    fake_comparator = MagicMock()
    fake_comparator.compare.return_value = ComparisonResult(summary="No changes.", differences=[])
    override_comparator(fake_comparator)

    client.post(
        "/compare",
        files={
            "file_a": ("v1.txt", b"Alpha text", "text/plain"),
            "file_b": ("v2.txt", b"Beta text", "text/plain"),
        },
        data={"language": "fr"},
    )

    args, kwargs = fake_comparator.compare.call_args
    assert "Alpha text" in args
    assert "Beta text" in args
    assert kwargs["language"] == "fr"


def test_compare_returns_415_when_either_file_is_unsupported():
    fake_factory = MagicMock()
    fake_factory.get_extractor.side_effect = UnsupportedFileTypeError("no extractor for .png")
    app.dependency_overrides[get_extractor_factory] = lambda: fake_factory

    try:
        response = client.post(
            "/compare",
            files={
                "file_a": ("v1.png", b"fake image bytes", "image/png"),
                "file_b": ("v2.txt", b"Version two text", "text/plain"),
            },
        )
        assert response.status_code == 415
    finally:
        app.dependency_overrides.clear()


def test_compare_returns_422_on_extraction_error():
    fake_extractor = MagicMock()
    fake_extractor.extract.side_effect = ExtractionError("corrupt file")
    fake_factory = MagicMock()
    fake_factory.get_extractor.return_value = fake_extractor
    app.dependency_overrides[get_extractor_factory] = lambda: fake_factory

    try:
        response = client.post(
            "/compare",
            files={
                "file_a": ("v1.pdf", b"not a real pdf", "application/pdf"),
                "file_b": ("v2.pdf", b"not a real pdf either", "application/pdf"),
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_compare_returns_502_on_comparison_error():
    fake_comparator = MagicMock()
    fake_comparator.compare.side_effect = ComparisonError("llm failed")
    override_comparator(fake_comparator)

    response = client.post(
        "/compare",
        files={
            "file_a": ("v1.txt", b"Version one text", "text/plain"),
            "file_b": ("v2.txt", b"Version two text", "text/plain"),
        },
    )

    assert response.status_code == 502
