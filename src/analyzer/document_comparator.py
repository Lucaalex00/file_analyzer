from pydantic import ValidationError

from src.analyzer.comparison_prompts import COMPARISON_SYSTEM_PROMPT, build_comparison_user_prompt
from src.analyzer.comparison_schemas import ComparisonResult
from src.observability.ai_tracing import log_ai_attempt, start_timer


class ComparisonError(Exception):
    pass


class DocumentComparator:
    def __init__(self, client, deployment: str, max_retries: int = 2):
        self._client = client
        self._deployment = deployment
        self._max_retries = max_retries

    def compare(self, text_a: str, text_b: str, language: str = "it") -> ComparisonResult:
        last_error: Exception | None = None
        max_attempts = self._max_retries + 1

        for attempt in range(max_attempts):
            started_at = start_timer()
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
                result = ComparisonResult.model_validate_json(content)
                log_ai_attempt(
                    "document_comparator", self._deployment, attempt + 1, max_attempts, started_at, "success"
                )
                return result
            except (ValidationError, ValueError) as exc:
                log_ai_attempt(
                    "document_comparator",
                    self._deployment,
                    attempt + 1,
                    max_attempts,
                    started_at,
                    "validation_error",
                    error=exc,
                )
                last_error = exc
                break  # a bad response won't fix itself on retry
            except Exception as exc:  # noqa: BLE001 - any client-side failure is retryable
                log_ai_attempt(
                    "document_comparator",
                    self._deployment,
                    attempt + 1,
                    max_attempts,
                    started_at,
                    "transient_error",
                    error=exc,
                )
                last_error = exc

        raise ComparisonError("Failed to compare documents") from last_error
