import json
from unittest.mock import MagicMock

import pytest

from src.analyzer.document_analyzer import AnalysisError, DocumentAnalyzer
from src.analyzer.prompts import MAX_DOCUMENT_CHARS, build_user_prompt
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


class TestBuildUserPrompt:
    def test_truncates_over_long_documents(self):
        prompt = build_user_prompt("x" * (MAX_DOCUMENT_CHARS + 5_000))

        assert prompt.endswith("x" * MAX_DOCUMENT_CHARS)
        assert not prompt.endswith("x" * (MAX_DOCUMENT_CHARS + 1))

    def test_keeps_short_documents_intact(self):
        prompt = build_user_prompt("short document")

        assert prompt.endswith("short document")

    def test_defaults_to_italian_when_no_language_given(self):
        prompt = build_user_prompt("short document")

        assert "Italian" in prompt

    def test_includes_the_requested_language_name(self):
        prompt = build_user_prompt("short document", language="fr")

        assert "French" in prompt

    def test_falls_back_to_the_raw_code_for_an_unknown_language(self):
        prompt = build_user_prompt("short document", language="xx")

        assert "xx" in prompt


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
