from pydantic import ValidationError

from src.analyzer.prompts import SYSTEM_PROMPT, build_user_prompt
from src.analyzer.quote_grounding import ground_quote
from src.analyzer.schemas import AnalysisResult
from src.extractors.base import RawText
from src.observability.ai_tracing import log_ai_attempt, start_timer


class AnalysisError(Exception):
    pass


def _ground_quotes(result: AnalysisResult, document_text: str) -> int:
    """Tie each quote back to the document, returning how many couldn't be.

    The schema validates shape, not truth: an invented quote passes it, reaches
    the report, and then silently fails to highlight because the frontend can't
    find it in the text. Quotes that are genuine but wrapped differently get
    realigned to the document's own wording (see quote_grounding.py); the ones
    that are nowhere in it lose their quote, keeping the finding but dropping
    evidence that can't be checked -- and, unlike the silent failure, leaving a
    count in the logs.
    """
    ungrounded = 0
    for flag in result.red_flags:
        if not flag.quote:
            continue
        grounded = ground_quote(flag.quote, document_text)
        if grounded is None:
            flag.quote = ""
            ungrounded += 1
        else:
            flag.quote = grounded
    return ungrounded


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
                    extra_body={"reasoning_effort": "low"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(raw_text.content, language=language)},
                    ],
                )
                content = completion.choices[0].message.content
                result = AnalysisResult.model_validate_json(content)
                ungrounded = _ground_quotes(result, raw_text.content)
                log_ai_attempt(
                    "document_analyzer",
                    self._deployment,
                    attempt + 1,
                    max_attempts,
                    started_at,
                    "success",
                    usage=getattr(completion, "usage", None),
                    ungrounded_quotes=ungrounded,
                )
                return result
            except (ValidationError, ValueError) as exc:
                # Retried like any other failure: the model is stochastic, so
                # an answer that came back malformed or off-schema often isn't
                # on the next roll. Giving up on the first one made a single
                # bad response cost the user the whole request.
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
