"""Serves a few of the project's own Markdown files to the web UI.

This is what the "docs" button in the header opens, so a visitor can read
what the project is and how it's built without leaving for GitHub.

Only the documents in `_DOCUMENTS` can ever be read: the id from the URL is
a key into that mapping, never a path. Building a path from the request
instead would turn this into an arbitrary-file-read endpoint.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import markdown

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_GITHUB_BLOB = "https://github.com/Lucaalex00/file_analyzer/blob/master/"
_GITHUB_RAW = "https://raw.githubusercontent.com/Lucaalex00/file_analyzer/master/"


@dataclass(frozen=True)
class ProjectDocument:
    id: str
    title: str
    filename: str
    section: str | None = None


_DOCUMENTS: tuple[ProjectDocument, ...] = (
    ProjectDocument(id="readme", title="What this is", filename="README.md"),
    ProjectDocument(id="overview", title="How it works", filename="OVERVIEW.md"),
    ProjectDocument(
        id="limitations",
        title="Known limitations",
        filename="README.md",
        section="Limitations",
    ),
)

_BY_ID = {document.id: document for document in _DOCUMENTS}

# Matches markdown links and images whose target is a repo-relative path --
# anything already absolute (http:, https:, mailto:, #anchor) is left alone.
_RELATIVE_TARGET = re.compile(r"(!?)\[([^\]]*)\]\((?!\w+:|#)([^)]+)\)")


def list_documents() -> list[ProjectDocument]:
    return list(_DOCUMENTS)


def get_document(document_id: str) -> ProjectDocument | None:
    return _BY_ID.get(document_id)


def _extract_section(text: str, heading: str) -> str:
    # Sections run from their own "## Heading" to the next heading of the
    # same level (or the end of the file).
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _absolutize_links(text: str) -> str:
    def replace(match: re.Match) -> str:
        bang, label, target = match.groups()
        base = _GITHUB_RAW if bang else _GITHUB_BLOB
        return f"{bang}[{label}]({base}{target.lstrip('./')})"

    return _RELATIVE_TARGET.sub(replace, text)


def render_document(document: ProjectDocument) -> str:
    text = (_REPO_ROOT / document.filename).read_text(encoding="utf-8")
    if document.section:
        text = _extract_section(text, document.section)
    return markdown.markdown(_absolutize_links(text), extensions=["tables", "fenced_code"])
