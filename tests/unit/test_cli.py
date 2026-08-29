from unittest.mock import MagicMock

from src.analyzer.comparison_schemas import ComparisonResult, Difference
from src.analyzer.schemas import AnalysisResult
from src.cli import build_parser, run_analyze, run_compare, run_extract
from src.extractors.base import RawText


def test_build_parser_parses_extract_command():
    parser = build_parser()
    args = parser.parse_args(["extract", "contract.pdf"])

    assert args.command == "extract"
    assert str(args.file) == "contract.pdf"


def test_build_parser_parses_analyze_command_with_defaults():
    parser = build_parser()
    args = parser.parse_args(["analyze", "contract.pdf"])

    assert args.command == "analyze"
    assert args.language == "it"
    assert args.format == "pdf"
    assert args.output is None


def test_build_parser_parses_analyze_command_with_options():
    parser = build_parser()
    args = parser.parse_args(["analyze", "contract.pdf", "--language", "en", "--format", "markdown", "--output", "out.md"])

    assert args.language == "en"
    assert args.format == "markdown"
    assert str(args.output) == "out.md"


def test_build_parser_parses_compare_command():
    parser = build_parser()
    args = parser.parse_args(["compare", "v1.txt", "v2.txt", "--language", "fr"])

    assert args.command == "compare"
    assert str(args.file_a) == "v1.txt"
    assert str(args.file_b) == "v2.txt"
    assert args.language == "fr"


def test_run_extract_returns_the_extracted_text(tmp_path):
    file_path = tmp_path / "note.txt"
    file_path.write_bytes(b"Hello, this is a contract.")

    fake_extractor = MagicMock()
    fake_extractor.extract.return_value = RawText(content="Hello, this is a contract.", source_filename="note.txt")
    fake_factory = MagicMock()
    fake_factory.get_extractor.return_value = fake_extractor

    args = MagicMock(file=file_path)
    text = run_extract(args, fake_factory)

    assert text == "Hello, this is a contract."


def test_run_analyze_writes_a_pdf_report_by_default(tmp_path):
    file_path = tmp_path / "note.txt"
    file_path.write_bytes(b"Some content")

    fake_pipeline = MagicMock()
    fake_pipeline.run.return_value = b"%PDF-1.4 fake"

    args = MagicMock(file=file_path, language="it", format="pdf", output=None)
    output_path = run_analyze(args, fake_pipeline)

    assert output_path.read_bytes() == b"%PDF-1.4 fake"
    assert output_path.suffix == ".pdf"
    fake_pipeline.run.assert_called_once()
    _, kwargs = fake_pipeline.run.call_args
    assert kwargs["language"] == "it"


def test_run_analyze_writes_markdown_when_requested(tmp_path):
    file_path = tmp_path / "note.txt"
    file_path.write_bytes(b"Some content")

    fake_analysis = AnalysisResult(detected_context="work", plain_explanation="e", summary="s", red_flags=[])
    fake_pipeline = MagicMock()
    fake_pipeline.run_with_analysis.return_value = (fake_analysis, b"unused")
    fake_pipeline.render_markdown.return_value = "# Analysis report"

    args = MagicMock(file=file_path, language="it", format="markdown", output=None)
    output_path = run_analyze(args, fake_pipeline)

    assert output_path.read_text(encoding="utf-8") == "# Analysis report"
    assert output_path.suffix == ".md"


def test_run_analyze_uses_the_explicit_output_path(tmp_path):
    file_path = tmp_path / "note.txt"
    file_path.write_bytes(b"Some content")
    explicit_output = tmp_path / "custom-name.pdf"

    fake_pipeline = MagicMock()
    fake_pipeline.run.return_value = b"%PDF-1.4 fake"

    args = MagicMock(file=file_path, language="it", format="pdf", output=explicit_output)
    output_path = run_analyze(args, fake_pipeline)

    assert output_path == explicit_output
    assert output_path.read_bytes() == b"%PDF-1.4 fake"


def test_run_compare_returns_comparison_as_json(tmp_path):
    file_a = tmp_path / "v1.txt"
    file_a.write_bytes(b"Version one")
    file_b = tmp_path / "v2.txt"
    file_b.write_bytes(b"Version two")

    fake_extractor = MagicMock()
    fake_extractor.extract.side_effect = [
        RawText(content="Version one", source_filename="v1.txt"),
        RawText(content="Version two", source_filename="v2.txt"),
    ]
    fake_factory = MagicMock()
    fake_factory.get_extractor.return_value = fake_extractor

    fake_comparator = MagicMock()
    fake_comparator.compare.return_value = ComparisonResult(
        summary="Nothing changed.",
        differences=[Difference(title="t", description="d", change_type="modified")],
    )

    args = MagicMock(file_a=file_a, file_b=file_b, language="it")
    output = run_compare(args, fake_comparator, fake_factory)

    assert "Nothing changed." in output
    assert "modified" in output
