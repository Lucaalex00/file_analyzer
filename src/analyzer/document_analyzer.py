from pydantic import ValidationError

from src.analyzer.prompts import SYSTEM_PROMPT, build_user_prompt
from src.analyzer.schemas import AnalysisResult
from src.extractors.base import RawText
from src.observability.ai_tracing import log_ai_attempt, start_timer


class AnalysisError(Exception):
    pass


class DocumentAnalyzer:
    def __init__(self, client, deployment: str, max_retries: int = 2):
        self._client = client
        self._deployment = deployment
        self._max_retries = max_retries

    def analyze(self, raw_text: RawText, language: str = "it") -> AnalysisResult:
        last_error: Exception | None = None
        max_attempts = self._max_retries + 1

        for attempt in range(max_attempts):
            started_at = start_timer()
            try:
                completion = self._client.chat.completions.create(
                    model=self._deployment,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(raw_text.content, language=language)},
                    ],
                )
                content = completion.choices[0].message.content
                result = AnalysisResult.model_validate_json(content)
                log_ai_attempt(
                    "document_analyzer", self._deployment, attempt + 1, max_attempts, started_at, "success"
                )
                return result
            except (ValidationError, ValueError) as exc:
                log_ai_attempt(
                    "document_analyzer",
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
                    "document_analyzer",
                    self._deployment,
                    attempt + 1,
                    max_attempts,
                    started_at,
                    "transient_error",
                    error=exc,
                )
                last_error = exc

        raise AnalysisError(f"Failed to analyze document {raw_text.source_filename!r}") from last_error
