from typing import Literal

from pydantic import BaseModel, Field


class Difference(BaseModel):
    title: str
    description: str
    change_type: Literal["added", "removed", "modified"]


class ComparisonResult(BaseModel):
    summary: str
    differences: list[Difference] = Field(default_factory=list)
