"""The sample documents the UI offers as one-click demos.

A visitor shouldn't have to find a file of their own -- let alone upload a
real contract to a stranger's site -- before seeing what the app does.

As with the docs viewer, the id in the URL is a key into this allowlist and
never a path. Entries whose file isn't present are simply not offered, so
the list degrades instead of 404-ing.
"""

from dataclasses import dataclass
from pathlib import Path

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "examples"

_MEDIA_TYPES = {
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".eml": "message/rfc822",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@dataclass(frozen=True)
class ExampleDocument:
    id: str
    filename: str

    @property
    def path(self) -> Path:
        return _EXAMPLES_DIR / self.filename

    @property
    def media_type(self) -> str:
        return _MEDIA_TYPES.get(self.path.suffix.lower(), "application/octet-stream")

    def exists(self) -> bool:
        return self.path.is_file()


_EXAMPLES: tuple[ExampleDocument, ...] = (
    ExampleDocument(id="lease", filename="sample_lease_contract.txt"),
    ExampleDocument(id="memo", filename="sample_work_memo.txt"),
    ExampleDocument(id="cv", filename="cv.pdf"),
)

_BY_ID = {example.id: example for example in _EXAMPLES}


def list_examples() -> list[ExampleDocument]:
    return [example for example in _EXAMPLES if example.exists()]


def get_example(example_id: str) -> ExampleDocument | None:
    example = _BY_ID.get(example_id)
    return example if example is not None and example.exists() else None
