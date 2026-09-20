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


def make_client_returning(payload: dict) -> MagicMock:
    client = MagicMock()
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    client.chat.completions.create.return_value = completion
    return client


LEASE_TEXT = b"This lease renews automatically unless cancelled by either party."


def test_a_rule_flag_the_model_also_found_is_merged_not_duplicated():
    # The model's title is free text in the requested language, so matching on
    # it can't work; what identifies "the same risk" is the passage quoted.
    client = make_client_returning(
        {
            "detected_context": "legal",
            "plain_explanation": "A lease.",
            "summary": "A lease that renews on its own.",
            "red_flags": [
                {
                    "title": "Automatic renewal with no notice period",
                    "description": "The lease renews unless actively cancelled.",
                    "severity": "medium",
                    "quote": "renews automatically unless cancelled",
                }
            ],
        }
    )
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=client, deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, _ = pipeline.run_with_analysis(
        file_bytes=LEASE_TEXT, filename="lease.txt", content_type="text/plain"
    )

    renewal_flags = [f for f in analysis.red_flags if "renew" in f.quote.lower()]
    assert len(renewal_flags) == 1, [f.title for f in analysis.red_flags]
    # Keeps the model's richer wording, but records that both agreed.
    assert renewal_flags[0].title == "Automatic renewal with no notice period"
    assert renewal_flags[0].source == "both"


def test_a_rule_flag_the_model_missed_is_added_and_marked_as_rule_based():
    client = make_client_returning(
        {
            "detected_context": "legal",
            "plain_explanation": "A lease.",
            "summary": "A lease.",
            "red_flags": [],
        }
    )
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=client, deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, _ = pipeline.run_with_analysis(
        file_bytes=LEASE_TEXT, filename="lease.txt", content_type="text/plain"
    )

    assert [f.source for f in analysis.red_flags] == ["rule"]


def test_merging_keeps_the_more_severe_of_the_two_verdicts():
    # The rule calls an early-termination penalty "high"; a model that rated
    # the same passage "low" must not talk the warning down.
    client = make_client_returning(
        {
            "detected_context": "legal",
            "plain_explanation": "A lease.",
            "summary": "A lease.",
            "red_flags": [
                {
                    "title": "Early termination cost",
                    "description": "There is a penalty.",
                    "severity": "low",
                    "quote": "penalty",
                }
            ],
        }
    )
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=client, deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, _ = pipeline.run_with_analysis(
        file_bytes=b"Early termination carries a penalty of two months of rent.",
        filename="lease.txt",
        content_type="text/plain",
    )

    penalty_flags = [f for f in analysis.red_flags if "penalty" in f.quote.lower()]
    assert len(penalty_flags) == 1
    assert penalty_flags[0].severity == "high"
    assert penalty_flags[0].source == "both"


def test_llm_flags_keep_their_own_source_when_no_rule_matches():
    client = make_client_returning(
        {
            "detected_context": "work",
            "plain_explanation": "A memo.",
            "summary": "A memo.",
            "red_flags": [
                {
                    "title": "Vague ownership",
                    "description": "Nobody is named as responsible.",
                    "severity": "low",
                    "quote": "someone should handle this",
                }
            ],
        }
    )
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=client, deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, _ = pipeline.run_with_analysis(
        file_bytes=b"Team, someone should handle this before Monday.",
        filename="memo.txt",
        content_type="text/plain",
    )

    assert [f.source for f in analysis.red_flags] == ["llm"]


def test_run_with_analysis_passes_the_requested_language_to_the_analyzer():
    client = make_fake_openai_client()
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=client, deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    pipeline.run_with_analysis(
        file_bytes=b"Team, please submit your reports by Friday.",
        filename="memo.txt",
        content_type="text/plain",
        language="fr",
    )

    _, kwargs = client.chat.completions.create.call_args
    user_message = next(m for m in kwargs["messages"] if m["role"] == "user")
    assert "French" in user_message["content"]


def test_run_with_analysis_from_text_skips_extraction_entirely():
    factory = MagicMock()
    pipeline = DocumentAnalysisPipeline(
        factory=factory,
        analyzer=DocumentAnalyzer(client=make_fake_openai_client(), deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, pdf_bytes = pipeline.run_with_analysis_from_text(
        text="Team, please submit your reports by Friday.",
        filename="memo.txt",
    )

    factory.get_extractor.assert_not_called()
    assert analysis.detected_context == "work"
    assert pdf_bytes.startswith(b"%PDF")


def test_run_with_analysis_from_text_merges_rule_based_flags():
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=make_fake_openai_client(), deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, _ = pipeline.run_with_analysis_from_text(
        text="This lease renews automatically unless cancelled by either party.",
        filename="lease.txt",
    )

    titles = [flag.title for flag in analysis.red_flags]
    assert "Rinnovo automatico" in titles


def test_render_markdown_reuses_the_pipelines_report_generator():
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=make_fake_openai_client(), deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    analysis, _ = pipeline.run_with_analysis(
        file_bytes=b"Team, please submit your reports by Friday.",
        filename="memo.txt",
        content_type="text/plain",
    )

    markdown = pipeline.render_markdown(analysis, "memo.txt")

    assert "A short memo reminding the team of a Friday deadline." in markdown
