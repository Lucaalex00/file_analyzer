import logging
import time

logger = logging.getLogger("file_analyzer.ai")

# Without this, these INFO-level records would be silently dropped in
# production: the root logger defaults to WARNING with no handler attached,
# so an app logger with no handler of its own is invisible outside tests
# (pytest's caplog installs its own capture handler, independent of this).
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


def start_timer() -> float:
    return time.perf_counter()


def log_ai_attempt(
    component: str,
    deployment: str,
    attempt: int,
    max_attempts: int,
    started_at: float,
    outcome: str,
    error: Exception | None = None,
    usage=None,
    ungrounded_quotes: int | None = None,
) -> None:
    """Log one attempt of an LLM call: which component, how long, and how it went.

    Never pass document content or raw error messages here -- both can echo
    back user data. Only the exception's class name (`error`) is logged, not
    its message, since client-library error bodies can include parts of the
    request that triggered them.

    `usage` is the provider's token count, when the response carries one (the
    demo client doesn't). Without it the hourly budget can only count calls,
    which treats an 80k-character document and a one-line note as equal.
    """
    duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
    error_type = type(error).__name__ if error is not None else None
    error_suffix = f" | error={error_type}" if error_type else ""

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)
    token_suffix = f" | tokens={total_tokens}" if total_tokens is not None else ""
    quote_suffix = f" | ungrounded_quotes={ungrounded_quotes}" if ungrounded_quotes else ""

    logger.info(
        "[AI] %s | attempt %d/%d | %s | %sms%s%s%s",
        component,
        attempt,
        max_attempts,
        outcome,
        duration_ms,
        token_suffix,
        quote_suffix,
        error_suffix,
        extra={
            "ai_component": component,
            "ai_deployment": deployment,
            "ai_attempt": attempt,
            "ai_max_attempts": max_attempts,
            "ai_outcome": outcome,
            "ai_duration_ms": duration_ms,
            "ai_error_type": error_type,
            "ai_prompt_tokens": prompt_tokens,
            "ai_completion_tokens": completion_tokens,
            "ai_total_tokens": total_tokens,
            "ai_ungrounded_quotes": ungrounded_quotes,
        },
    )
