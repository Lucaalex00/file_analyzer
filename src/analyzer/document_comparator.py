from pydantic import ValidationError

from src.analyzer.comparison_prompts import COMPARISON_SYSTEM_PROMPT, build_comparison_user_prompt
from src.analyzer.comparison_schemas import ComparisonResult


class ComparisonError(Exception):
    pass


class DocumentComparator:
    def __init__(self, client, deployment: str, max_retries: int = 2):
        self._client = client
        self._deployment = deployment
        self._max_retries = max_retries

    def compare(self, text_a: str, text_b: str, language: str = "it") -> ComparisonResult:
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                completion = self._client.chat.completions.create(
                    model=self._deployment,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": build_comparison_user_prompt(text_a, text_b, language=language),
                        },
                    ],
                )
                content = completion.choices[0].message.content
                return ComparisonResult.model_validate_json(content)
            except (ValidationError, ValueError) as exc:
                last_error = exc
                break  # a bad response won't fix itself on retry
            except Exception as exc:  # noqa: BLE001 - any client-side failure is retryable
                last_error = exc

        raise ComparisonError("Failed to compare documents") from last_error
