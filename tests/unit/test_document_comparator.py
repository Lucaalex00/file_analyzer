import json
from unittest.mock import MagicMock

import pytest

from src.analyzer.document_comparator import ComparisonError, DocumentComparator

VALID_RESPONSE_JSON = json.dumps(
    {
        "summary": "The renewal clause was made automatic and the penalty was increased.",
        "differences": [
            {
                "title": "Automatic renewal",
                "description": "Version B renews automatically; version A required manual renewal.",
                "change_type": "modified",
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


def test_returns_parsed_comparison_result_on_valid_response():
    client = make_client(response_content=VALID_RESPONSE_JSON)
    comparator = DocumentComparator(client=client, deployment="gpt-4o-mini")

    result = comparator.compare("Version A text", "Version B text")

    assert "renewal" in result.summary.lower()
    assert result.differences[0].change_type == "modified"


def test_calls_client_with_both_versions_in_the_user_prompt():
    client = make_client(response_content=VALID_RESPONSE_JSON)
    comparator = DocumentComparator(client=client, deployment="gpt-4o-mini")

    comparator.compare("Alpha content", "Beta content")

    _, kwargs = client.chat.completions.create.call_args
    user_message = next(m for m in kwargs["messages"] if m["role"] == "user")
    assert "Alpha content" in user_message["content"]
    assert "Beta content" in user_message["content"]


def test_raises_comparison_error_on_invalid_json():
    client = make_client(response_content="not json")
    comparator = DocumentComparator(client=client, deployment="gpt-4o-mini", max_retries=0)

    with pytest.raises(ComparisonError):
        comparator.compare("A", "B")


def test_raises_comparison_error_after_retries_exhausted():
    client = make_client(raise_exc=RuntimeError("timeout"))
    comparator = DocumentComparator(client=client, deployment="gpt-4o-mini", max_retries=1)

    with pytest.raises(ComparisonError):
        comparator.compare("A", "B")

    assert client.chat.completions.create.call_count == 2
