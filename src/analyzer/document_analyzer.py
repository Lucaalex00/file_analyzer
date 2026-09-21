from pydantic import ValidationError

from src.analyzer.prompts import SYSTEM_PROMPT, build_user_prompt
from src.analyzer.quote_grounding import ground_quote
from src.analyzer.schemas import AnalysisResult
from src.extractors.base import RawText
from src.observability.ai_tracing import log_ai_attempt, start_timer


class AnalysisError(Exception):
    pass


class AnalysisRefusedError(AnalysisError):
    """The provider declined to analyze this document at all.

    Distinct from a failure, because it is a verdict rather than an outage:
    retrying changes nothing, and the pipeline answers it by falling back to
    the deterministic checks instead of giving the user nothing.
    """


def _is_retryable(exc: Exception) -> bool:
    """Whether trying the same request again could plausibly succeed.

    Rate limiting and server-side failures pass; a 4xx does not. Azure
    OpenAI's jailbreak shield, for instance, answers 400 content_filter on
    documents that look like prompt-injection attempts -- a verdict that is
    identical on every retry, so retrying only spends the hourly budget.

    Read off `status_code` rather than the provider's exception classes, so
    this stays true for the Azure client, the Groq one and the demo one
    alike; an exception without a status (a timeout, a dropped connection)
    is treated as retryable.
    """
    status = getattr(exc, "status_code", None)
    if status is None:
        return True
    return status == 429 or status >= 500


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

    def analyze(
        self, raw_text: RawText, language: str = "it", metrics: dict | None = None
    ) -> AnalysisResult:
        """Analyze the document. If `metrics` is given, token counts are
        written into it.

        The caller owns the dict, so nothing about this is shared between
        concurrent requests -- which storing the last call's usage on the
        analyzer (a cached singleton) would have been.
        """
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
                usage = getattr(completion, "usage", None)
                if metrics is not None:
                    metrics["total_tokens"] = getattr(usage, "total_tokens", None)
                    metrics["attempts"] = attempt + 1
                log_ai_attempt(
                    "document_analyzer",
                    self._deployment,
                    attempt + 1,
                    max_attempts,
                    started_at,
                    "success",
                    usage=usage,
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
            except Exception as exc:  # noqa: BLE001 - the provider's failures aren't a fixed set
                retryable = _is_retryable(exc)
                log_ai_attempt(
                    "document_analyzer",
                    self._deployment,
                    attempt + 1,
                    max_attempts,
                    started_at,
                    "transient_error" if retryable else "refused",
                    error=exc,
                )
                last_error = exc
                if not retryable:
                    raise AnalysisRefusedError(
                        f"The AI provider refused to analyze {raw_text.source_filename!r}"
                    ) from exc

        raise AnalysisError(f"Failed to analyze document {raw_text.source_filename!r}") from last_error
