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


class AnalysisResult(BaseModel):
    detected_context: Literal["legal", "work", "personal", "other"]
    plain_explanation: str
    summary: str
    red_flags: list[RedFlag] = Field(default_factory=list)
