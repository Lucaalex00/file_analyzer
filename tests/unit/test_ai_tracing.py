import logging

from src.observability.ai_tracing import log_ai_attempt, start_timer


def test_logs_a_readable_line_with_all_expected_fields(caplog):
    started_at = start_timer()

    with caplog.at_level(logging.INFO, logger="file_analyzer.ai"):
        log_ai_attempt(
            component="document_analyzer",
            deployment="gpt-4o-mini",
            attempt=1,
            max_attempts=3,
            started_at=started_at,
            outcome="success",
        )

    assert len(caplog.records) == 1
    record = caplog.records[0]

    assert record.ai_component == "document_analyzer"
    assert record.ai_deployment == "gpt-4o-mini"
    assert record.ai_attempt == 1
    assert record.ai_max_attempts == 3
    assert record.ai_outcome == "success"
    assert record.ai_error_type is None
    assert isinstance(record.ai_duration_ms, float)
    assert record.ai_duration_ms >= 0

    # The rendered message must be readable on its own, not just structured
    # fields -- this is what a human sees scrolling through logs.
    message = record.getMessage()
    assert "document_analyzer" in message
    assert "1/3" in message
    assert "success" in message


def test_logs_the_error_type_but_never_the_error_message(caplog):
    # Error messages from an LLM client can echo back parts of the request
    # (including document content in some client libraries' error bodies).
    # Only the exception's class name is safe to log.
    started_at = start_timer()
    error = ValueError("this text must never appear in logs: SSN 123-45-6789")

    with caplog.at_level(logging.INFO, logger="file_analyzer.ai"):
        log_ai_attempt(
            component="document_analyzer",
            deployment="gpt-4o-mini",
            attempt=1,
            max_attempts=3,
            started_at=started_at,
            outcome="validation_error",
            error=error,
        )

    record = caplog.records[0]
    assert record.ai_error_type == "ValueError"
    assert "123-45-6789" not in record.getMessage()
    assert "123-45-6789" not in caplog.text


def test_omits_error_type_when_no_error_given(caplog):
    started_at = start_timer()

    with caplog.at_level(logging.INFO, logger="file_analyzer.ai"):
        log_ai_attempt(
            component="document_comparator",
            deployment="gpt-4o-mini",
            attempt=1,
            max_attempts=1,
            started_at=started_at,
            outcome="success",
        )

    record = caplog.records[0]
    assert record.ai_error_type is None
    assert "error=" not in record.getMessage()
