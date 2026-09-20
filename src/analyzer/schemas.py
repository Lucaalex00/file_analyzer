from typing import Literal

from pydantic import BaseModel, Field


class RedFlag(BaseModel):
    title: str
    description: str
    severity: Literal["low", "medium", "high"]
    quote: str = ""
    # Who raised it: the model, the rule-based pass, or both independently.
    # Defaults to "llm" because the model's JSON never carries this field --
    # it's set by the pipeline when the two sources are merged.
    source: Literal["llm", "rule", "both"] = "llm"
    # Which deterministic check fired, when one did. Survives both the
    # merge (where the model's wording wins) and translation, so "did the
    # safety net catch this?" stays answerable in any language.
    rule_id: str | None = None


class AnalysisResult(BaseModel):
    detected_context: Literal["legal", "work", "personal", "other"]
    plain_explanation: str
    summary: str
    red_flags: list[RedFlag] = Field(default_factory=list)
