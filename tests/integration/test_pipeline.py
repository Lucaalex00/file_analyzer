import json
from unittest.mock import MagicMock

from src.analyzer.document_analyzer import DocumentAnalyzer
from src.extractors.factory import ExtractorFactory
from src.pipeline import DocumentAnalysisPipeline
from src.report.report_generator import ReportGenerator

VALID_RESPONSE_JSON = json.dumps(
    {
        "detected_context": "work",
        "plain_explanation": "This is an internal memo about a deadline.",
        "summary": "A short memo reminding the team of a Friday deadline.",
        "red_flags": [],
    }
)


def make_fake_openai_client():
    client = MagicMock()
    message = MagicMock()
    message.content = VALID_RESPONSE_JSON
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    client.chat.completions.create.return_value = completion
    return client


def test_pipeline_runs_end_to_end_for_txt_file():
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=make_fake_openai_client(), deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    pdf_bytes = pipeline.run(
        file_bytes=b"Team, please submit your reports by Friday.",
        filename="memo.txt",
        content_type="text/plain",
    )

    assert pdf_bytes.startswith(b"%PDF")


def test_run_with_analysis_returns_both_the_analysis_and_the_pdf():
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=make_fake_openai_client(), deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, pdf_bytes = pipeline.run_with_analysis(
        file_bytes=b"Team, please submit your reports by Friday.",
        filename="memo.txt",
        content_type="text/plain",
    )

    assert analysis.detected_context == "work"
    assert analysis.summary == "A short memo reminding the team of a Friday deadline."
    assert pdf_bytes.startswith(b"%PDF")


def test_run_with_analysis_merges_rule_based_flags_with_llm_flags():
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=make_fake_openai_client(), deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, _ = pipeline.run_with_analysis(
        file_bytes=b"This lease renews automatically unless cancelled by either party.",
        filename="lease.txt",
        content_type="text/plain",
    )

    titles = [flag.title for flag in analysis.red_flags]
    assert "Rinnovo automatico" in titles
