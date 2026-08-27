from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RawText:
    content: str
    source_filename: str


class ExtractionError(Exception):
    """Raised when a file cannot be extracted (corrupt, empty, unreadable)."""


class BaseExtractor(ABC):
    @abstractmethod
    def supports(self, filename: str, content_type: str | None) -> bool:
        ...

    @abstractmethod
    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        ...
