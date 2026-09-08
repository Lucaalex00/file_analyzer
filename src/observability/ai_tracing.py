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
) -> None:
    """Log one attempt of an LLM call: which component, how long, and how it went.

    Never pass document content or raw error messages here -- both can echo
    back user data. Only the exception's class name (`error`) is logged, not
    its message, since client-library error bodies can include parts of the
    request that triggered them.
    """
    duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
    error_type = type(error).__name__ if error is not None else None
    error_suffix = f" | error={error_type}" if error_type else ""

    logger.info(
        "[AI] %s | attempt %d/%d | %s | %sms%s",
        component,
        attempt,
        max_attempts,
        outcome,
        duration_ms,
        error_suffix,
        extra={
            "ai_component": component,
            "ai_deployment": deployment,
            "ai_attempt": attempt,
            "ai_max_attempts": max_attempts,
            "ai_outcome": outcome,
            "ai_duration_ms": duration_ms,
            "ai_error_type": error_type,
        },
    )
