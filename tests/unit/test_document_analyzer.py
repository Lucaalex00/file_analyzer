import json
import logging
from datetime import date
from unittest.mock import MagicMock

import pytest

from src.analyzer.document_analyzer import AnalysisError, AnalysisRefusedError, DocumentAnalyzer
from src.analyzer.prompts import MAX_DOCUMENT_CHARS, SYSTEM_PROMPT, build_user_prompt
from src.extractors.base import RawText

VALID_RESPONSE_JSON = json.dumps(
    {
        "detected_context": "legal",
        "plain_explanation": "This is a rental agreement in plain terms.",
        "summary": "A one-year apartment lease between landlord and tenant.",
        "red_flags": [
            {
                "title": "Early termination penalty",
                "description": "Breaking the lease early costs two months rent.",
                "severity": "high",
            }
        ],
    }
)


def make_client(response_content: str | None = None, raise_exc: Exception | None = None):
    client = MagicMock()
    if raise_exc is not None:
        client.chat.completions.create.side_effect = raise_exc
    else:
        message = MagicMock()
        message.content = response_content
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]
        client.chat.completions.create.return_value = completion
    return client


class TestSystemPromptGuardrails:
    def test_instructs_the_model_to_avoid_generic_filler(self):
        # Real testing against a live model surfaced explanations that were
        # accurate but generic ("this document outlines the terms") instead
        # of grounded in the document's own specifics. Regression guard so
        # this instruction can't be silently dropped from the prompt.
        lowered = SYSTEM_PROMPT.lower()
        assert "generic" in lowered
        assert "specific" in lowered

    def test_instructs_the_model_to_cite_concrete_details(self):
        lowered = SYSTEM_PROMPT.lower()
        assert "dates" in lowered
        assert "amounts" in lowered


class TestBuildUserPrompt:
    def test_truncates_over_long_documents(self):
        prompt = build_user_prompt("x" * (MAX_DOCUMENT_CHARS + 5_000))

        assert ("x" * MAX_DOCUMENT_CHARS) in prompt
        assert ("x" * (MAX_DOCUMENT_CHARS + 1)) not in prompt

    def test_keeps_short_documents_intact(self):
        prompt = build_user_prompt("short document")

        assert "short document" in prompt

    def test_wraps_the_document_text_in_delimiter_tags(self):
        # A clear boundary between instructions and untrusted document
        # content is a basic prompt-injection mitigation.
        prompt = build_user_prompt("some document text")

        assert "<document>" in prompt
        assert "</document>" in prompt
        assert prompt.index("<document>") < prompt.index("some document text") < prompt.index("</document>")

    def test_defaults_to_italian_when_no_language_given(self):
        prompt = build_user_prompt("short document")

        assert "Italian" in prompt

    def test_includes_the_requested_language_name(self):
        prompt = build_user_prompt("short document", language="fr")

        assert "French" in prompt

    def test_falls_back_to_the_raw_code_for_an_unknown_language(self):
        prompt = build_user_prompt("short document", language="xx")

        assert "xx" in prompt

    def test_tells_the_model_what_todays_date_is(self):
        # Without it the model judges "expired", "upcoming" and "future-dated"
        # against its training cutoff, and gets them wrong.
        prompt = build_user_prompt("short document", today=date(2026, 9, 16))

        assert "2026-09-16" in prompt

    def test_uses_the_real_current_date_by_default(self):
        prompt = build_user_prompt("short document")

        assert date.today().isoformat() in prompt


class TestAnalyze:
    def test_returns_parsed_analysis_result_on_valid_response(self):
        client = make_client(response_content=VALID_RESPONSE_JSON)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")
        raw_text = RawText(content="Lease agreement text...", source_filename="lease.pdf")

        result = analyzer.analyze(raw_text)

        assert result.detected_context == "legal"
        assert result.summary == "A one-year apartment lease between landlord and tenant."
        assert len(result.red_flags) == 1
        assert result.red_flags[0].severity == "high"

    def test_calls_client_with_deployment_and_json_response_format(self):
        client = make_client(response_content=VALID_RESPONSE_JSON)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")
        raw_text = RawText(content="Some text", source_filename="doc.txt")

        analyzer.analyze(raw_text)

        _, kwargs = client.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4o-mini"

    def test_calls_client_with_low_reasoning_effort_for_latency(self):
        client = make_client(response_content=VALID_RESPONSE_JSON)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")
        raw_text = RawText(content="Some text", source_filename="doc.txt")

        analyzer.analyze(raw_text)

        _, kwargs = client.chat.completions.create.call_args
        assert kwargs["extra_body"] == {"reasoning_effort": "low"}

    def test_passes_the_requested_language_into_the_user_prompt(self):
        client = make_client(response_content=VALID_RESPONSE_JSON)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")
        raw_text = RawText(content="Some text", source_filename="doc.txt")

        analyzer.analyze(raw_text, language="fr")

        _, kwargs = client.chat.completions.create.call_args
        user_message = next(m for m in kwargs["messages"] if m["role"] == "user")
        assert "French" in user_message["content"]
        assert kwargs["response_format"] == {"type": "json_object"}

    def test_raises_analysis_error_on_invalid_json(self):
        client = make_client(response_content="not json at all")
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=0)
        raw_text = RawText(content="text", source_filename="doc.txt")

        with pytest.raises(AnalysisError):
            analyzer.analyze(raw_text)

    def test_raises_analysis_error_after_client_exception_retries_exhausted(self):
        client = make_client(raise_exc=RuntimeError("timeout"))
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=1)
        raw_text = RawText(content="text", source_filename="doc.txt")

        with pytest.raises(AnalysisError):
            analyzer.analyze(raw_text)

        assert client.chat.completions.create.call_count == 2  # initial + 1 retry

    def test_drops_a_quote_the_document_does_not_contain(self):
        # The schema can only check shape; nothing stopped an invented quote
        # from reaching the report, where it silently failed to highlight.
        client = make_client(
            response_content=json.dumps(
                {
                    "detected_context": "legal",
                    "plain_explanation": "explanation",
                    "summary": "summary",
                    "red_flags": [
                        {
                            "title": "Penalty",
                            "description": "There is a penalty.",
                            "severity": "high",
                            "quote": "a sentence the document never contained",
                        }
                    ],
                }
            )
        )
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")

        result = analyzer.analyze(RawText(content="Early termination costs two months.", source_filename="d.txt"))

        # The finding survives; only the unverifiable evidence is removed.
        assert result.red_flags[0].title == "Penalty"
        assert result.red_flags[0].quote == ""

    def test_keeps_a_quote_that_appears_verbatim(self):
        client = make_client(
            response_content=json.dumps(
                {
                    "detected_context": "legal",
                    "plain_explanation": "explanation",
                    "summary": "summary",
                    "red_flags": [
                        {
                            "title": "Penalty",
                            "description": "There is a penalty.",
                            "severity": "high",
                            "quote": "two months",
                        }
                    ],
                }
            )
        )
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")

        result = analyzer.analyze(RawText(content="Early termination costs two months.", source_filename="d.txt"))

        assert result.red_flags[0].quote == "two months"

    def test_logs_when_a_quote_had_to_be_dropped(self, caplog):
        client = make_client(
            response_content=json.dumps(
                {
                    "detected_context": "legal",
                    "plain_explanation": "explanation",
                    "summary": "summary",
                    "red_flags": [
                        {"title": "A", "description": "d", "severity": "low", "quote": "never said this"},
                        {"title": "B", "description": "d", "severity": "low", "quote": "two months"},
                    ],
                }
            )
        )
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")

        with caplog.at_level(logging.INFO, logger="file_analyzer.ai"):
            analyzer.analyze(RawText(content="Early termination costs two months.", source_filename="d.txt"))

        success = [r for r in caplog.records if r.name == "file_analyzer.ai"][-1]
        assert success.ai_ungrounded_quotes == 1

    def test_retries_when_the_model_answers_out_of_format(self):
        # An LLM is stochastic: a malformed answer often isn't malformed on
        # the next roll, so one bad response shouldn't cost the user the
        # whole request.
        client = MagicMock()
        bad = MagicMock()
        bad.choices = [MagicMock(message=MagicMock(content="not json at all"))]
        good = MagicMock()
        good.choices = [MagicMock(message=MagicMock(content=VALID_RESPONSE_JSON))]
        client.chat.completions.create.side_effect = [bad, good]

        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)

        result = analyzer.analyze(RawText(content="text", source_filename="doc.txt"))

        assert result.detected_context == "legal"
        assert client.chat.completions.create.call_count == 2

    def test_gives_up_after_exhausting_retries_on_malformed_output(self):
        client = make_client(response_content="not json at all")
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)

        with pytest.raises(AnalysisError):
            analyzer.analyze(RawText(content="text", source_filename="doc.txt"))

        assert client.chat.completions.create.call_count == 3

    def test_a_provider_refusal_raises_its_own_error_type(self):
        # The pipeline degrades to rule-based-only on a refusal, but must not
        # do that for an ordinary failure, so the two can't share a type.
        refused = RuntimeError("content_filter")
        refused.status_code = 400
        client = make_client(raise_exc=refused)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)

        with pytest.raises(AnalysisRefusedError):
            analyzer.analyze(RawText(content="text", source_filename="doc.txt"))

    def test_an_exhausted_retry_is_not_a_refusal(self):
        client = make_client(raise_exc=RuntimeError("timeout"))
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=1)

        with pytest.raises(AnalysisError) as raised:
            analyzer.analyze(RawText(content="text", source_filename="doc.txt"))

        assert not isinstance(raised.value, AnalysisRefusedError)

    def test_does_not_retry_a_permanent_client_error(self):
        # Azure OpenAI answers 400 with code=content_filter when its jailbreak
        # shield trips on a document. Retrying that burns three calls -- and
        # three units of the hourly budget -- on an outcome that cannot change.
        refused = RuntimeError("content_filter")
        refused.status_code = 400
        client = make_client(raise_exc=refused)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)

        with pytest.raises(AnalysisError):
            analyzer.analyze(RawText(content="text", source_filename="doc.txt"))

        assert client.chat.completions.create.call_count == 1

    def test_still_retries_rate_limiting_and_server_errors(self):
        throttled = RuntimeError("rate limited")
        throttled.status_code = 429
        client = make_client(raise_exc=throttled)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)

        with pytest.raises(AnalysisError):
            analyzer.analyze(RawText(content="text", source_filename="doc.txt"))

        assert client.chat.completions.create.call_count == 3

    def test_succeeds_after_one_transient_failure(self):
        client = MagicMock()
        message = MagicMock()
        message.content = VALID_RESPONSE_JSON
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]
        client.chat.completions.create.side_effect = [RuntimeError("timeout"), completion]

        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)
        raw_text = RawText(content="text", source_filename="doc.txt")

        result = analyzer.analyze(raw_text)

        assert result.detected_context == "legal"
        assert client.chat.completions.create.call_count == 2


class TestTracing:
    def test_logs_one_success_record_on_the_happy_path(self, caplog):
        client = make_client(response_content=VALID_RESPONSE_JSON)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")
        raw_text = RawText(content="Lease agreement text with sensitive names...", source_filename="lease.pdf")

        with caplog.at_level(logging.INFO, logger="file_analyzer.ai"):
            analyzer.analyze(raw_text)

        records = [r for r in caplog.records if r.name == "file_analyzer.ai"]
        assert len(records) == 1
        assert records[0].ai_component == "document_analyzer"
        assert records[0].ai_outcome == "success"
        assert records[0].ai_attempt == 1
        # The document content must never end up in a log line.
        assert "sensitive names" not in caplog.text

    def test_logs_a_record_per_attempt_including_the_retry(self, caplog):
        client = MagicMock()
        message = MagicMock()
        message.content = VALID_RESPONSE_JSON
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]
        client.chat.completions.create.side_effect = [RuntimeError("timeout"), completion]
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)
        raw_text = RawText(content="text", source_filename="doc.txt")

        with caplog.at_level(logging.INFO, logger="file_analyzer.ai"):
            analyzer.analyze(raw_text)

        records = [r for r in caplog.records if r.name == "file_analyzer.ai"]
        assert [r.ai_outcome for r in records] == ["transient_error", "success"]
        assert [r.ai_attempt for r in records] == [1, 2]

    def test_logs_one_validation_error_record_per_attempt(self, caplog):
        client = make_client(response_content="not json at all")
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)
        raw_text = RawText(content="text", source_filename="doc.txt")

        with caplog.at_level(logging.INFO, logger="file_analyzer.ai"):
            with pytest.raises(AnalysisError):
                analyzer.analyze(raw_text)

        records = [r for r in caplog.records if r.name == "file_analyzer.ai"]
        assert [r.ai_outcome for r in records] == ["validation_error"] * 3
