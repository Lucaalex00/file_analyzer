import json
from unittest.mock import MagicMock

from src.analyzer.budgeted_client import BudgetedAIClient
from src.api.ai_budget import AIBudget

ANALYSIS_PROMPT = 'Return {"detected_context": ..., "red_flags": [...]}'


def make_real_client():
    client = MagicMock()
    message = MagicMock()
    message.content = json.dumps({"detected_context": "work", "red_flags": []})
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    client.chat.completions.create.return_value = completion
    return client


def call(client):
    return client.chat.completions.create(
        model="gpt-5-mini",
        response_format={"type": "json_object"},
        extra_body={"reasoning_effort": "low"},
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": "<document>\nSome text\n</document>\nRespond in Italian"},
        ],
    )


def test_calls_the_real_client_while_budget_remains():
    real = make_real_client()
    client = BudgetedAIClient(real_client=real, budget=AIBudget(max_calls=2))

    call(client)

    assert real.chat.completions.create.call_count == 1


def test_falls_back_to_the_demo_client_once_the_budget_is_spent():
    real = make_real_client()
    client = BudgetedAIClient(real_client=real, budget=AIBudget(max_calls=1))

    call(client)
    completion = call(client)

    # The second call never reached the paid provider...
    assert real.chat.completions.create.call_count == 1
    # ...but still produced a usable, clearly-simulated answer.
    payload = json.loads(completion.choices[0].message.content)
    assert "demo" in payload["plain_explanation"].lower()
