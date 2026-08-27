from typing import Literal

from pydantic import BaseModel, Field


class RedFlag(BaseModel):
    title: str
    description: str
    severity: Literal["low", "medium", "high"]


class AnalysisResult(BaseModel):
    detected_context: Literal["legal", "work", "personal", "other"]
    plain_explanation: str
    summary: str
    red_flags: list[RedFlag] = Field(default_factory=list)
