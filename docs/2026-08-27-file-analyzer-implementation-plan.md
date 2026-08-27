# File Analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stateless service that accepts a PDF/TXT/DOCX upload, uses Azure OpenAI to produce a plain-language explanation, summary, and red-flag list, and returns a generated PDF report — with a one-command local demo and full CI.

**Architecture:** Modular pipeline (`Extractor → Analyzer → ReportGenerator`) behind a single FastAPI endpoint, no database or persistent storage. Each stage is a small, independently testable component wired together by a thin orchestrator.

**Tech Stack:** Python 3.12, FastAPI, uvicorn, pypdf, python-docx, Jinja2 + WeasyPrint (PDF rendering), `openai` SDK (`AzureOpenAI` client), pytest + httpx, Docker/Docker Compose, GitHub Actions, Azure Functions (Python v2, ASGI) + Bicep for the demo deploy.

**Spec:** [docs/2026-08-27-file-analyzer-design.md](../2026-08-27-file-analyzer-design.md)

## Global Constraints

- No database, no persistent file storage anywhere in the pipeline — everything lives in memory for the duration of one request.
- No authentication on the API — single public endpoint, stateless.
- MVP file types only: `.pdf`, `.txt`, `.docx`. OCR and email parsing are explicitly out of scope (Fase 2).
- Context detection (legal/work/personal) is automatic, decided by the LLM from content — no manual mode selection.
- Report output format: PDF only.
- `docs/` stays flat: one `YYYY-MM-DD-topic.md` per feature/commit-push (Context / What changed / Known gap / Verification), plus `docs/adr/` for architectural decisions. No `specs/` or `contracts/` folders.
- Every component must be unit-testable in isolation — Azure OpenAI is always mocked in unit tests, never called for real.

---

### Task 1: Project scaffolding + health check

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `Makefile`
- Create: `pytest.ini`
- Create: `src/__init__.py`
- Create: `src/api/__init__.py`
- Create: `src/api/main.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Test: `tests/integration/test_health.py`

**Interfaces:**
- Produces: `src/api/main.py` exposes a module-level `app` (FastAPI instance) with `GET /health` returning `{"status": "ok"}`. Later tasks import `app` from `src.api.main` and add routes/exception handlers to it.

- [ ] **Step 1: Write `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
python-docx==1.1.2
pypdf==5.0.1
weasyprint==62.3
jinja2==3.1.4
openai==1.51.0
python-multipart==0.0.12
```

- [ ] **Step 2: Write `requirements-dev.txt`**

```
-r requirements.txt
pytest==8.3.3
pytest-cov==5.0.0
httpx==0.27.2
ruff==0.6.9
```

- [ ] **Step 3: Write `Dockerfile`**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Write `docker-compose.yml`**

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./src:/app/src
    command: ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 5: Write `.env.example`**

```
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=replace-me
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-08-01-preview
MAX_FILE_SIZE_BYTES=10485760
```

- [ ] **Step 6: Write `.gitignore`**

```
__pycache__/
*.pyc
.venv/
venv/
.env
.pytest_cache/
.ruff_cache/
htmlcov/
.coverage
```

- [ ] **Step 7: Write `Makefile`**

```makefile
.DEFAULT_GOAL := help
.PHONY: help up down demo test lint env

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

env: ## Create a .env from .env.example (does nothing if .env already exists)
	@test -f .env || (cp .env.example .env && echo "Created .env — edit it with your Azure OpenAI credentials.")

up: ## Build and start the API (http://localhost:8000)
	docker compose up --build

down: ## Stop the stack
	docker compose down

test: ## Run the full test suite locally (needs a venv with requirements-dev.txt installed)
	pytest

lint: ## Run ruff
	ruff check src tests
```

- [ ] **Step 8: Write `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 9: Write `src/__init__.py`, `src/api/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`**

All five files are empty.

- [ ] **Step 10: Write the failing test `tests/integration/test_health.py`**

```python
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 11: Run the test to verify it fails**

Run: `pip install -r requirements-dev.txt && pytest tests/integration/test_health.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.api.main'` or similar — the module doesn't exist yet)

- [ ] **Step 12: Write `src/api/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="File Analyzer")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 13: Run the test to verify it passes**

Run: `pytest tests/integration/test_health.py -v`
Expected: PASS

- [ ] **Step 14: Verify the Docker stack boots**

Run: `cp .env.example .env && docker compose up --build -d && curl http://localhost:8000/health && docker compose down`
Expected: `{"status":"ok"}` printed, container starts without errors

- [ ] **Step 15: Commit**

```bash
git add requirements.txt requirements-dev.txt Dockerfile docker-compose.yml .env.example .gitignore Makefile pytest.ini src tests
git commit -m "chore: project scaffolding with health check endpoint"
```

---

### Task 2: TextExtractor (.txt, .docx)

**Files:**
- Create: `src/extractors/__init__.py`
- Create: `src/extractors/base.py`
- Create: `src/extractors/text_extractor.py`
- Test: `tests/unit/test_text_extractor.py`

**Interfaces:**
- Produces:
  - `src/extractors/base.py`: `RawText` (frozen dataclass, fields `content: str`, `source_filename: str`), `BaseExtractor` (ABC with `supports(self, filename: str, content_type: str | None) -> bool` and `extract(self, file_bytes: bytes, filename: str) -> RawText`), `ExtractionError(Exception)`.
  - `src/extractors/text_extractor.py`: `TextExtractor(BaseExtractor)` — supports `.txt` and `.docx` (by extension, case-insensitive).

- [ ] **Step 1: Write `src/extractors/__init__.py`**

Empty file.

- [ ] **Step 2: Write `src/extractors/base.py`**

```python
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
```

- [ ] **Step 3: Write the failing tests `tests/unit/test_text_extractor.py`**

```python
import io

import pytest
from docx import Document

from src.extractors.base import ExtractionError
from src.extractors.text_extractor import TextExtractor


def make_docx_bytes(paragraphs: list[str]) -> bytes:
    doc = Document()
    for paragraph in paragraphs:
        doc.add_paragraph(paragraph)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


class TestSupports:
    def test_supports_txt_extension(self):
        extractor = TextExtractor()
        assert extractor.supports("contract.txt", "text/plain") is True

    def test_supports_docx_extension(self):
        extractor = TextExtractor()
        assert extractor.supports("contract.DOCX", None) is True

    def test_does_not_support_pdf_extension(self):
        extractor = TextExtractor()
        assert extractor.supports("contract.pdf", "application/pdf") is False


class TestExtractTxt:
    def test_extracts_plain_text_content(self):
        extractor = TextExtractor()
        raw = extractor.extract(b"Hello, this is a contract.", "note.txt")

        assert raw.content == "Hello, this is a contract."
        assert raw.source_filename == "note.txt"

    def test_raises_extraction_error_on_empty_txt(self):
        extractor = TextExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"   \n  ", "empty.txt")


class TestExtractDocx:
    def test_extracts_docx_paragraphs_joined(self):
        extractor = TextExtractor()
        docx_bytes = make_docx_bytes(["First paragraph.", "Second paragraph."])

        raw = extractor.extract(docx_bytes, "contract.docx")

        assert raw.content == "First paragraph.\nSecond paragraph."
        assert raw.source_filename == "contract.docx"

    def test_raises_extraction_error_on_empty_docx(self):
        extractor = TextExtractor()
        docx_bytes = make_docx_bytes([])

        with pytest.raises(ExtractionError):
            extractor.extract(docx_bytes, "empty.docx")

    def test_raises_extraction_error_on_corrupt_docx(self):
        extractor = TextExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"not a real docx file", "broken.docx")
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `pytest tests/unit/test_text_extractor.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.extractors.text_extractor'`)

- [ ] **Step 5: Write `src/extractors/text_extractor.py`**

```python
import io

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from src.extractors.base import BaseExtractor, ExtractionError, RawText

_SUPPORTED_EXTENSIONS = (".txt", ".docx")


class TextExtractor(BaseExtractor):
    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(_SUPPORTED_EXTENSIONS)

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        if filename.lower().endswith(".docx"):
            content = self._extract_docx(file_bytes)
        else:
            content = self._extract_txt(file_bytes)

        if not content.strip():
            raise ExtractionError(f"No readable text found in {filename!r}")

        return RawText(content=content, source_filename=filename)

    def _extract_txt(self, file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8", errors="ignore")

    def _extract_docx(self, file_bytes: bytes) -> str:
        try:
            document = Document(io.BytesIO(file_bytes))
        except PackageNotFoundError as exc:
            raise ExtractionError("File is not a valid .docx document") from exc

        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/unit/test_text_extractor.py -v`
Expected: PASS (7 tests)

- [ ] **Step 7: Commit**

```bash
git add src/extractors/__init__.py src/extractors/base.py src/extractors/text_extractor.py tests/unit/test_text_extractor.py
git commit -m "feat: add TextExtractor for .txt and .docx files"
```

---

### Task 3: PdfExtractor

**Files:**
- Create: `src/extractors/pdf_extractor.py`
- Test: `tests/unit/test_pdf_extractor.py`

**Interfaces:**
- Consumes: `src.extractors.base.BaseExtractor`, `RawText`, `ExtractionError` (Task 2)
- Produces: `src/extractors/pdf_extractor.py`: `PdfExtractor(BaseExtractor)` — supports `.pdf` by extension.

- [ ] **Step 1: Write the failing tests `tests/unit/test_pdf_extractor.py`**

```python
import io

import pytest
from pypdf import PdfWriter

from src.extractors.base import ExtractionError
from src.extractors.pdf_extractor import PdfExtractor


def make_pdf_bytes(pages_text: list[str]) -> bytes:
    writer = PdfWriter()
    for text in pages_text:
        writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class TestSupports:
    def test_supports_pdf_extension(self):
        extractor = PdfExtractor()
        assert extractor.supports("contract.PDF", "application/pdf") is True

    def test_does_not_support_txt_extension(self):
        extractor = PdfExtractor()
        assert extractor.supports("contract.txt", "text/plain") is False


class TestExtract:
    def test_raises_extraction_error_on_corrupt_pdf(self):
        extractor = PdfExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"not a real pdf", "broken.pdf")

    def test_raises_extraction_error_on_blank_pdf(self):
        extractor = PdfExtractor()
        pdf_bytes = make_pdf_bytes(["", ""])

        with pytest.raises(ExtractionError):
            extractor.extract(pdf_bytes, "blank.pdf")

    def test_extracts_text_from_real_pdf(self, tmp_path):
        # Blank-page PdfWriter can't embed real text easily without reportlab,
        # so this test builds a minimal one-page PDF with a text stream by hand.
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
            b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"5 0 obj<</Length 44>>stream\n"
            b"BT /F1 12 Tf 10 100 Td (Hello Contract) Tj ET\n"
            b"endstream endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n"
            b"trailer<</Size 6/Root 1 0 R>>\n"
            b"startxref\n0\n%%EOF"
        )

        extractor = PdfExtractor()
        raw = extractor.extract(pdf_bytes, "contract.pdf")

        assert "Hello Contract" in raw.content
        assert raw.source_filename == "contract.pdf"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/unit/test_pdf_extractor.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.extractors.pdf_extractor'`)

- [ ] **Step 3: Write `src/extractors/pdf_extractor.py`**

```python
import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.extractors.base import BaseExtractor, ExtractionError, RawText


class PdfExtractor(BaseExtractor):
    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(".pdf")

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        except (PdfReadError, ValueError) as exc:
            raise ExtractionError(f"Could not read PDF {filename!r}") from exc

        if not content.strip():
            raise ExtractionError(
                f"No extractable text found in {filename!r} "
                "(it may be a scanned image without OCR support)"
            )

        return RawText(content=content, source_filename=filename)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/unit/test_pdf_extractor.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/extractors/pdf_extractor.py tests/unit/test_pdf_extractor.py
git commit -m "feat: add PdfExtractor"
```

---

### Task 4: ExtractorFactory

**Files:**
- Create: `src/extractors/factory.py`
- Test: `tests/unit/test_extractor_factory.py`

**Interfaces:**
- Consumes: `BaseExtractor`, `PdfExtractor` (Task 3), `TextExtractor` (Task 2)
- Produces: `src/extractors/factory.py`: `UnsupportedFileTypeError(Exception)`, `ExtractorFactory` with `__init__(self, extractors: list[BaseExtractor] | None = None)` and `get_extractor(self, filename: str, content_type: str | None) -> BaseExtractor`.

- [ ] **Step 1: Write the failing tests `tests/unit/test_extractor_factory.py`**

```python
import pytest

from src.extractors.base import BaseExtractor, RawText
from src.extractors.factory import ExtractorFactory, UnsupportedFileTypeError
from src.extractors.pdf_extractor import PdfExtractor
from src.extractors.text_extractor import TextExtractor


class FakeExtractor(BaseExtractor):
    def __init__(self, extension: str):
        self.extension = extension

    def supports(self, filename, content_type):
        return filename.lower().endswith(self.extension)

    def extract(self, file_bytes, filename):
        return RawText(content="fake", source_filename=filename)


def test_default_factory_selects_pdf_extractor():
    factory = ExtractorFactory()
    extractor = factory.get_extractor("contract.pdf", "application/pdf")
    assert isinstance(extractor, PdfExtractor)


def test_default_factory_selects_text_extractor_for_txt():
    factory = ExtractorFactory()
    extractor = factory.get_extractor("note.txt", "text/plain")
    assert isinstance(extractor, TextExtractor)


def test_default_factory_selects_text_extractor_for_docx():
    factory = ExtractorFactory()
    extractor = factory.get_extractor("note.docx", None)
    assert isinstance(extractor, TextExtractor)


def test_raises_unsupported_file_type_for_unknown_extension():
    factory = ExtractorFactory()

    with pytest.raises(UnsupportedFileTypeError):
        factory.get_extractor("photo.png", "image/png")


def test_uses_injected_extractors_list_and_first_match_wins():
    factory = ExtractorFactory(extractors=[FakeExtractor(".log")])
    extractor = factory.get_extractor("run.log", None)
    assert isinstance(extractor, FakeExtractor)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/unit/test_extractor_factory.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.extractors.factory'`)

- [ ] **Step 3: Write `src/extractors/factory.py`**

```python
from src.extractors.base import BaseExtractor
from src.extractors.pdf_extractor import PdfExtractor
from src.extractors.text_extractor import TextExtractor


class UnsupportedFileTypeError(Exception):
    pass


class ExtractorFactory:
    def __init__(self, extractors: list[BaseExtractor] | None = None):
        self._extractors = extractors if extractors is not None else [PdfExtractor(), TextExtractor()]

    def get_extractor(self, filename: str, content_type: str | None) -> BaseExtractor:
        for extractor in self._extractors:
            if extractor.supports(filename, content_type):
                return extractor
        raise UnsupportedFileTypeError(f"No extractor available for {filename!r}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/unit/test_extractor_factory.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/extractors/factory.py tests/unit/test_extractor_factory.py
git commit -m "feat: add ExtractorFactory"
```

---

### Task 5: Analyzer schemas + DocumentAnalyzer (Azure OpenAI, mocked)

**Files:**
- Create: `src/analyzer/__init__.py`
- Create: `src/analyzer/schemas.py`
- Create: `src/analyzer/prompts.py`
- Create: `src/analyzer/document_analyzer.py`
- Test: `tests/unit/test_document_analyzer.py`

**Interfaces:**
- Consumes: `RawText` (Task 2)
- Produces:
  - `src/analyzer/schemas.py`: `RedFlag` (pydantic `BaseModel`: `title: str`, `description: str`, `severity: Literal["low", "medium", "high"]`), `AnalysisResult` (pydantic `BaseModel`: `detected_context: Literal["legal", "work", "personal", "other"]`, `plain_explanation: str`, `summary: str`, `red_flags: list[RedFlag]`).
  - `src/analyzer/document_analyzer.py`: `AnalysisError(Exception)`, `DocumentAnalyzer` with `__init__(self, client, deployment: str, max_retries: int = 2)` and `analyze(self, raw_text: RawText) -> AnalysisResult`. `client` is any object exposing `.chat.completions.create(model=..., messages=..., response_format=...)` (the shape of `openai.AzureOpenAI`) — later tasks construct the real client from env vars and pass it in.

- [ ] **Step 1: Write `src/analyzer/__init__.py`**

Empty file.

- [ ] **Step 2: Write `src/analyzer/schemas.py`**

```python
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
```

- [ ] **Step 3: Write `src/analyzer/prompts.py`**

```python
SYSTEM_PROMPT = """You are a document analysis assistant. You read a document and \
explain it to a non-expert. You must respond with a single JSON object matching \
exactly this schema:

{
  "detected_context": "legal" | "work" | "personal" | "other",
  "plain_explanation": string,  // clear explanation in plain language, no jargon
  "summary": string,            // 2-4 sentence summary of the document
  "red_flags": [
    {"title": string, "description": string, "severity": "low" | "medium" | "high"}
  ]
}

detected_context is your best guess at the document's domain based on its content \
(a contract or court notice is "legal", a work email or report is "work", a personal \
letter or medical result is "personal", anything else is "other"). red_flags lists \
concerning clauses, deadlines, unusual requests, or risks a non-expert should notice \
- return an empty list if there are none. Respond with JSON only, no other text."""


def build_user_prompt(document_text: str) -> str:
    return f"Analyze the following document:\n\n{document_text}"
```

- [ ] **Step 4: Write the failing tests `tests/unit/test_document_analyzer.py`**

```python
import json
from unittest.mock import MagicMock

import pytest

from src.analyzer.document_analyzer import AnalysisError, DocumentAnalyzer
from src.extractors.base import RawText

VALID_RESPONSE_JSON = json.dumps(
    {
        "detected_context": "legal",
        "plain_explanation": "This is a rental agreement in plain terms.",
        "summary": "A one-year apartment lease between landlord and tenant.",
        "red_flags": [
            {
                "title": "Early termination penalty",
                "description": "Breaking the lease early costs two months rent.",
                "severity": "high",
            }
        ],
    }
)


def make_client(response_content: str | None = None, raise_exc: Exception | None = None):
    client = MagicMock()
    if raise_exc is not None:
        client.chat.completions.create.side_effect = raise_exc
    else:
        message = MagicMock()
        message.content = response_content
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]
        client.chat.completions.create.return_value = completion
    return client


class TestAnalyze:
    def test_returns_parsed_analysis_result_on_valid_response(self):
        client = make_client(response_content=VALID_RESPONSE_JSON)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")
        raw_text = RawText(content="Lease agreement text...", source_filename="lease.pdf")

        result = analyzer.analyze(raw_text)

        assert result.detected_context == "legal"
        assert result.summary == "A one-year apartment lease between landlord and tenant."
        assert len(result.red_flags) == 1
        assert result.red_flags[0].severity == "high"

    def test_calls_client_with_deployment_and_json_response_format(self):
        client = make_client(response_content=VALID_RESPONSE_JSON)
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini")
        raw_text = RawText(content="Some text", source_filename="doc.txt")

        analyzer.analyze(raw_text)

        _, kwargs = client.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["response_format"] == {"type": "json_object"}

    def test_raises_analysis_error_on_invalid_json(self):
        client = make_client(response_content="not json at all")
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=0)
        raw_text = RawText(content="text", source_filename="doc.txt")

        with pytest.raises(AnalysisError):
            analyzer.analyze(raw_text)

    def test_raises_analysis_error_after_client_exception_retries_exhausted(self):
        client = make_client(raise_exc=RuntimeError("timeout"))
        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=1)
        raw_text = RawText(content="text", source_filename="doc.txt")

        with pytest.raises(AnalysisError):
            analyzer.analyze(raw_text)

        assert client.chat.completions.create.call_count == 2  # initial + 1 retry

    def test_succeeds_after_one_transient_failure(self):
        client = MagicMock()
        message = MagicMock()
        message.content = VALID_RESPONSE_JSON
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]
        client.chat.completions.create.side_effect = [RuntimeError("timeout"), completion]

        analyzer = DocumentAnalyzer(client=client, deployment="gpt-4o-mini", max_retries=2)
        raw_text = RawText(content="text", source_filename="doc.txt")

        result = analyzer.analyze(raw_text)

        assert result.detected_context == "legal"
        assert client.chat.completions.create.call_count == 2
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `pytest tests/unit/test_document_analyzer.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.analyzer.document_analyzer'`)

- [ ] **Step 6: Write `src/analyzer/document_analyzer.py`**

```python
from pydantic import ValidationError

from src.analyzer.prompts import SYSTEM_PROMPT, build_user_prompt
from src.analyzer.schemas import AnalysisResult
from src.extractors.base import RawText


class AnalysisError(Exception):
    pass


class DocumentAnalyzer:
    def __init__(self, client, deployment: str, max_retries: int = 2):
        self._client = client
        self._deployment = deployment
        self._max_retries = max_retries

    def analyze(self, raw_text: RawText) -> AnalysisResult:
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                completion = self._client.chat.completions.create(
                    model=self._deployment,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(raw_text.content)},
                    ],
                )
                content = completion.choices[0].message.content
                return AnalysisResult.model_validate_json(content)
            except (ValidationError, ValueError) as exc:
                last_error = exc
                break  # a bad response won't fix itself on retry
            except Exception as exc:  # noqa: BLE001 - any client-side failure is retryable
                last_error = exc

        raise AnalysisError(f"Failed to analyze document {raw_text.source_filename!r}") from last_error
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest tests/unit/test_document_analyzer.py -v`
Expected: PASS (5 tests)

- [ ] **Step 8: Commit**

```bash
git add src/analyzer tests/unit/test_document_analyzer.py
git commit -m "feat: add DocumentAnalyzer with Azure OpenAI-backed analysis"
```

---

### Task 6: ReportGenerator (Jinja2 + WeasyPrint)

**Files:**
- Create: `src/report/__init__.py`
- Create: `src/report/templates/report.html.j2`
- Create: `src/report/report_generator.py`
- Test: `tests/unit/test_report_generator.py`

**Interfaces:**
- Consumes: `AnalysisResult` (Task 5)
- Produces: `src/report/report_generator.py`: `ReportGenerator` with `__init__(self)` and `generate(self, analysis: AnalysisResult, original_filename: str) -> bytes` (returns PDF bytes).

- [ ] **Step 1: Write `src/report/__init__.py`**

Empty file.

- [ ] **Step 2: Write `src/report/templates/report.html.j2`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Analysis report — {{ original_filename }}</title>
<style>
  body { font-family: sans-serif; margin: 2.5cm; color: #1a1a1a; }
  h1 { font-size: 20px; }
  h2 { font-size: 15px; margin-top: 1.5em; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
  .meta { color: #666; font-size: 12px; }
  .red-flag { margin-bottom: 0.8em; padding: 0.6em; border-left: 4px solid #999; }
  .red-flag.high { border-color: #c0392b; }
  .red-flag.medium { border-color: #d68910; }
  .red-flag.low { border-color: #7f8c8d; }
  .red-flag .title { font-weight: bold; }
  .red-flag .severity { text-transform: uppercase; font-size: 10px; color: #666; }
</style>
</head>
<body>
  <h1>Analysis report</h1>
  <p class="meta">Source file: {{ original_filename }} — Detected context: {{ analysis.detected_context }}</p>

  <h2>Summary</h2>
  <p>{{ analysis.summary }}</p>

  <h2>Explanation</h2>
  <p>{{ analysis.plain_explanation }}</p>

  <h2>Things to pay attention to</h2>
  {% if analysis.red_flags %}
    {% for flag in analysis.red_flags %}
    <div class="red-flag {{ flag.severity }}">
      <div class="title">{{ flag.title }}</div>
      <div class="severity">{{ flag.severity }}</div>
      <div>{{ flag.description }}</div>
    </div>
    {% endfor %}
  {% else %}
    <p>No notable red flags found.</p>
  {% endif %}
</body>
</html>
```

- [ ] **Step 3: Write the failing tests `tests/unit/test_report_generator.py`**

```python
from src.analyzer.schemas import AnalysisResult, RedFlag
from src.report.report_generator import ReportGenerator


def test_generate_returns_non_empty_pdf_bytes():
    analysis = AnalysisResult(
        detected_context="legal",
        plain_explanation="This document is a rental agreement.",
        summary="A one-year lease between landlord and tenant.",
        red_flags=[
            RedFlag(title="Early termination penalty", description="Costs two months rent.", severity="high")
        ],
    )
    generator = ReportGenerator()

    pdf_bytes = generator.generate(analysis, original_filename="lease.pdf")

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_generate_handles_no_red_flags():
    analysis = AnalysisResult(
        detected_context="personal",
        plain_explanation="A friendly letter.",
        summary="Short personal note.",
        red_flags=[],
    )
    generator = ReportGenerator()

    pdf_bytes = generator.generate(analysis, original_filename="letter.txt")

    assert pdf_bytes.startswith(b"%PDF")
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `pytest tests/unit/test_report_generator.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.report.report_generator'`)

- [ ] **Step 5: Write `src/report/report_generator.py`**

```python
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from src.analyzer.schemas import AnalysisResult

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class ReportGenerator:
    def __init__(self):
        self._env = Environment(
            loader=FileSystemLoader(_TEMPLATE_DIR),
            autoescape=select_autoescape(["html"]),
        )
        self._template = self._env.get_template("report.html.j2")

    def generate(self, analysis: AnalysisResult, original_filename: str) -> bytes:
        html = self._template.render(analysis=analysis, original_filename=original_filename)
        return HTML(string=html).write_pdf()
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/unit/test_report_generator.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Commit**

```bash
git add src/report tests/unit/test_report_generator.py
git commit -m "feat: add ReportGenerator (Jinja2 + WeasyPrint)"
```

---

### Task 7: Pipeline orchestrator

**Files:**
- Create: `src/pipeline.py`
- Test: `tests/integration/test_pipeline.py`

**Interfaces:**
- Consumes: `ExtractorFactory` (Task 4), `DocumentAnalyzer` (Task 5), `ReportGenerator` (Task 6)
- Produces: `src/pipeline.py`: `DocumentAnalysisPipeline` with `__init__(self, factory: ExtractorFactory, analyzer: DocumentAnalyzer, report_generator: ReportGenerator)` and `run(self, file_bytes: bytes, filename: str, content_type: str | None) -> bytes` (returns PDF bytes). Propagates `UnsupportedFileTypeError`, `ExtractionError`, `AnalysisError` unchanged — the API layer (Task 8) is responsible for mapping them to HTTP responses.

- [ ] **Step 1: Write the failing test `tests/integration/test_pipeline.py`**

```python
import json
from unittest.mock import MagicMock

from src.analyzer.document_analyzer import DocumentAnalyzer
from src.extractors.factory import ExtractorFactory
from src.pipeline import DocumentAnalysisPipeline
from src.report.report_generator import ReportGenerator

VALID_RESPONSE_JSON = json.dumps(
    {
        "detected_context": "work",
        "plain_explanation": "This is an internal memo about a deadline.",
        "summary": "A short memo reminding the team of a Friday deadline.",
        "red_flags": [],
    }
)


def make_fake_openai_client():
    client = MagicMock()
    message = MagicMock()
    message.content = VALID_RESPONSE_JSON
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    client.chat.completions.create.return_value = completion
    return client


def test_pipeline_runs_end_to_end_for_txt_file():
    pipeline = DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=make_fake_openai_client(), deployment="gpt-4o-mini"),
        report_generator=ReportGenerator(),
    )

    pdf_bytes = pipeline.run(
        file_bytes=b"Team, please submit your reports by Friday.",
        filename="memo.txt",
        content_type="text/plain",
    )

    assert pdf_bytes.startswith(b"%PDF")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/integration/test_pipeline.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.pipeline'`)

- [ ] **Step 3: Write `src/pipeline.py`**

```python
from src.analyzer.document_analyzer import DocumentAnalyzer
from src.extractors.factory import ExtractorFactory
from src.report.report_generator import ReportGenerator


class DocumentAnalysisPipeline:
    def __init__(
        self,
        factory: ExtractorFactory,
        analyzer: DocumentAnalyzer,
        report_generator: ReportGenerator,
    ):
        self._factory = factory
        self._analyzer = analyzer
        self._report_generator = report_generator

    def run(self, file_bytes: bytes, filename: str, content_type: str | None) -> bytes:
        extractor = self._factory.get_extractor(filename, content_type)
        raw_text = extractor.extract(file_bytes, filename)
        analysis = self._analyzer.analyze(raw_text)
        return self._report_generator.generate(analysis, original_filename=filename)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/integration/test_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/integration/test_pipeline.py
git commit -m "feat: add DocumentAnalysisPipeline orchestrator"
```

---

### Task 8: FastAPI `/analyze` endpoint + error handling

**Files:**
- Modify: `src/api/main.py`
- Create: `src/api/config.py`
- Create: `src/api/dependencies.py`
- Test: `tests/integration/test_api.py`

**Interfaces:**
- Consumes: `DocumentAnalysisPipeline` (Task 7), `UnsupportedFileTypeError` (Task 4), `ExtractionError` (Task 2), `AnalysisError` (Task 5)
- Produces: `POST /analyze` — multipart file upload, returns `application/pdf` on success (200); `413` if the file exceeds `MAX_FILE_SIZE_BYTES`; `415` for `UnsupportedFileTypeError`; `422` for `ExtractionError`; `502` for `AnalysisError`. `src/api/dependencies.py` exposes `get_pipeline() -> DocumentAnalysisPipeline`, overridable in tests via FastAPI's `app.dependency_overrides`.

- [ ] **Step 1: Write `src/api/config.py`**

```python
import os
from functools import lru_cache


class Settings:
    def __init__(self):
        self.azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.azure_openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        self.max_file_size_bytes = int(os.environ.get("MAX_FILE_SIZE_BYTES", 10 * 1024 * 1024))


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: Write `src/api/dependencies.py`**

```python
from functools import lru_cache

from openai import AzureOpenAI

from src.analyzer.document_analyzer import DocumentAnalyzer
from src.api.config import get_settings
from src.extractors.factory import ExtractorFactory
from src.pipeline import DocumentAnalysisPipeline
from src.report.report_generator import ReportGenerator


@lru_cache
def get_pipeline() -> DocumentAnalysisPipeline:
    settings = get_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    return DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=client, deployment=settings.azure_openai_deployment),
        report_generator=ReportGenerator(),
    )
```

- [ ] **Step 3: Write the failing tests `tests/integration/test_api.py`**

```python
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.analyzer.document_analyzer import AnalysisError
from src.api.dependencies import get_pipeline
from src.api.main import app
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError

client = TestClient(app)


def override_pipeline(fake_pipeline):
    app.dependency_overrides[get_pipeline] = lambda: fake_pipeline


def teardown_function():
    app.dependency_overrides.clear()


def test_analyze_returns_pdf_on_success():
    fake_pipeline = MagicMock()
    fake_pipeline.run.return_value = b"%PDF-1.4 fake pdf content"
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("note.txt", b"Hello world", "text/plain")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 fake pdf content"


def test_analyze_returns_413_when_file_too_large(monkeypatch):
    monkeypatch.setenv("MAX_FILE_SIZE_BYTES", "10")
    from src.api.config import get_settings
    get_settings.cache_clear()

    fake_pipeline = MagicMock()
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("note.txt", b"this is definitely more than ten bytes", "text/plain")},
    )

    assert response.status_code == 413
    get_settings.cache_clear()


def test_analyze_returns_415_for_unsupported_file_type():
    fake_pipeline = MagicMock()
    fake_pipeline.run.side_effect = UnsupportedFileTypeError("no extractor for .png")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("photo.png", b"fake image bytes", "image/png")},
    )

    assert response.status_code == 415


def test_analyze_returns_422_on_extraction_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run.side_effect = ExtractionError("corrupt file")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("broken.pdf", b"not a real pdf", "application/pdf")},
    )

    assert response.status_code == 422


def test_analyze_returns_502_on_analysis_error():
    fake_pipeline = MagicMock()
    fake_pipeline.run.side_effect = AnalysisError("llm failed")
    override_pipeline(fake_pipeline)

    response = client.post(
        "/analyze",
        files={"file": ("note.txt", b"Hello world", "text/plain")},
    )

    assert response.status_code == 502
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `pytest tests/integration/test_api.py -v`
Expected: FAIL (404 on `/analyze` — route doesn't exist yet)

- [ ] **Step 5: Rewrite `src/api/main.py`**

```python
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import Response

from src.analyzer.document_analyzer import AnalysisError
from src.api.config import get_settings
from src.api.dependencies import get_pipeline
from src.extractors.base import ExtractionError
from src.extractors.factory import UnsupportedFileTypeError
from src.pipeline import DocumentAnalysisPipeline

app = FastAPI(title="File Analyzer")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(
    file: UploadFile,
    pipeline: DocumentAnalysisPipeline = Depends(get_pipeline),
) -> Response:
    settings = get_settings()
    file_bytes = await file.read()

    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the maximum allowed size")

    try:
        pdf_bytes = pipeline.run(
            file_bytes=file_bytes,
            filename=file.filename or "upload",
            content_type=file.content_type,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnalysisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return Response(content=pdf_bytes, media_type="application/pdf")
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/integration/test_api.py -v`
Expected: PASS (5 tests)

- [ ] **Step 7: Run the full test suite**

Run: `pytest -v`
Expected: PASS (all tests across all previous tasks, no regressions)

- [ ] **Step 8: Commit**

```bash
git add src/api tests/integration/test_api.py
git commit -m "feat: add POST /analyze endpoint with error handling"
```

---

### Task 9: Example files + demo assets

**Files:**
- Create: `examples/sample_lease_contract.txt`
- Create: `examples/sample_work_memo.txt`
- Create: `examples/README.md`
- Create: `scripts/generate_examples.py`

**Interfaces:**
- Consumes: `DocumentAnalysisPipeline`, `get_pipeline` wiring (Task 8) — reused, not reimplemented.

- [ ] **Step 1: Write `examples/sample_lease_contract.txt`**

```
RESIDENTIAL LEASE AGREEMENT

This agreement is entered into between Landlord (Acme Properties LLC) and Tenant
(Jane Doe) for the property located at 12 Elm Street, Apt 4.

Term: 12 months, starting September 1, 2026.
Monthly rent: 950 EUR, due on the 1st of each month.

Early termination: If the Tenant terminates this lease before the end of the term,
the Tenant must pay a penalty equal to two (2) months of rent, in addition to
forfeiting the security deposit.

Automatic renewal: Unless either party provides written notice 60 days before the
end of the term, this lease automatically renews for another 12 months at a rent
increase of 8%.

Maintenance: Tenant is responsible for all repairs under 200 EUR, including
appliance failures not caused by normal wear and tear.
```

- [ ] **Step 2: Write `examples/sample_work_memo.txt`**

```
Subject: Q4 Deliverable Deadline Moved Up

Team,

Due to a client request, the Q4 deliverable deadline has moved from December 15
to November 30. Please reprioritize your current tasks accordingly and flag to
your manager by end of week if this creates a scheduling conflict.

Also, a reminder that the shared credentials for the staging environment must be
rotated by anyone with access — send your new password to IT directly, not over
Slack.

Thanks,
Project Management
```

- [ ] **Step 3: Write `scripts/generate_examples.py`**

```python
"""Regenerate the example PDF reports in examples/ by running the real pipeline
against the sample input files. Requires a working .env with real Azure OpenAI
credentials — this is a manual/local step, not run in CI.

Usage: python scripts/generate_examples.py
"""

from pathlib import Path

from src.api.dependencies import get_pipeline

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

SAMPLE_FILES = [
    "sample_lease_contract.txt",
    "sample_work_memo.txt",
]


def main() -> None:
    pipeline = get_pipeline()

    for filename in SAMPLE_FILES:
        source_path = EXAMPLES_DIR / filename
        file_bytes = source_path.read_bytes()

        pdf_bytes = pipeline.run(file_bytes=file_bytes, filename=filename, content_type="text/plain")

        output_path = source_path.with_suffix(".report.pdf")
        output_path.write_bytes(pdf_bytes)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write `examples/README.md`**

```markdown
# Examples

Two sample input files (`sample_lease_contract.txt`, `sample_work_memo.txt`) and
their generated analysis reports (`*.report.pdf`), so you can see the tool's
output without configuring Azure OpenAI credentials yourself.

To regenerate the reports against your own Azure OpenAI resource:

\`\`\`bash
cp .env.example .env  # fill in your real credentials
python scripts/generate_examples.py
\`\`\`
```

- [ ] **Step 5: Generate the report PDFs (manual, requires real Azure OpenAI credentials)**

Run: `cp .env.example .env` (fill in real credentials), then `pip install -r requirements-dev.txt && python scripts/generate_examples.py`
Expected: `examples/sample_lease_contract.report.pdf` and `examples/sample_work_memo.report.pdf` created. If you don't have Azure OpenAI credentials yet, skip this step for now and come back to it before the README/demo task (Task 11) — the repo is still fully functional and tested without it.

- [ ] **Step 6: Commit**

```bash
git add examples scripts/generate_examples.py
git commit -m "docs: add example input files and report generation script"
```

---

### Task 10: CI pipeline (lint, test, docker build, push GHCR)

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `docker-compose.prebuilt.yml`

**Interfaces:**
- Consumes: `Dockerfile`, `requirements-dev.txt`, `pytest.ini` (Task 1)

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install system dependencies for WeasyPrint
        run: |
          sudo apt-get update
          sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
      - name: Install Python dependencies
        run: pip install -r requirements-dev.txt
      - name: Lint
        run: ruff check src tests
      - name: Test
        run: pytest -v

  docker:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
```

- [ ] **Step 2: Write `docker-compose.prebuilt.yml`**

```yaml
services:
  api:
    image: ghcr.io/OWNER/file-analyzer:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
```

Note: replace `OWNER/file-analyzer` with the real GitHub repository path once the repo is pushed (Task 11 updates this alongside the README).

- [ ] **Step 3: Add the `demo` target to `Makefile`**

Modify `Makefile`, add after the `up` target:

```makefile
demo: ## Start the API from the CI-published image — no local build
	docker compose -f docker-compose.yml -f docker-compose.prebuilt.yml up -d
	@echo "API http://localhost:8000"
```

And add `demo` to the `.PHONY` line.

- [ ] **Step 4: Verify the workflow file is valid YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
Expected: no error

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml docker-compose.prebuilt.yml Makefile
git commit -m "ci: add GitHub Actions pipeline (lint, test, docker build/push GHCR)"
```

---

### Task 11: README, OVERVIEW, ADR, push to GitHub

**Files:**
- Create: `README.md`
- Create: `OVERVIEW.md`
- Create: `docs/adr/0001-pdf-generation-weasyprint.md`
- Modify: `docker-compose.prebuilt.yml`

**Interfaces:**
- Consumes: everything built in Tasks 1-10 — this task documents and publishes the finished MVP, no new code.

- [ ] **Step 1: Write `docs/adr/0001-pdf-generation-weasyprint.md`**

```markdown
# 0001 — PDF generation via WeasyPrint

## Status

Accepted

## Context

The service needs to turn a structured `AnalysisResult` into a downloadable PDF
report. The two mainstream Python options are ReportLab (imperative, low-level
drawing API) and WeasyPrint (renders HTML/CSS to PDF).

## Decision

Use WeasyPrint with a Jinja2 HTML template. Report layout (headings, red-flag
cards, severity colors) is expressed as ordinary HTML/CSS, which is faster to
write and change than ReportLab's canvas-drawing API, and keeps the report's
visual design in one template file instead of scattered across Python code.

## Consequences

WeasyPrint depends on system libraries (Pango, Cairo, GDK-Pixbuf) that must be
installed in any environment that runs it — handled in `Dockerfile` and in the
CI workflow's `apt-get install` step. This is a known friction point on Azure
Functions' Consumption plan, which restricts custom system dependencies more
than a plain container; if Fase 2 deployment work runs into this, the fallback
is `xhtml2pdf`, a pure-Python HTML-to-PDF renderer with no native dependencies,
at the cost of weaker CSS support.
```

- [ ] **Step 2: Write `README.md`**

```markdown
# File Analyzer

Upload a document — a lease, a work memo, a personal letter — and get back a
plain-language explanation, a summary, and a list of things worth paying
attention to, as a downloadable PDF report. No account, no database, nothing
stored: the file exists only for the duration of the request.

## Quick start

\`\`\`bash
git clone <this-repo-url> && cd file-analyzer
make env    # creates .env — fill in your Azure OpenAI credentials
make up     # builds and starts the API at http://localhost:8000
\`\`\`

Try it:

\`\`\`bash
curl -F "file=@examples/sample_lease_contract.txt" http://localhost:8000/analyze -o report.pdf
\`\`\`

No Azure OpenAI credentials yet? See [`examples/`](examples/) for sample input
files and their already-generated report PDFs.

## What it does

- Accepts `.pdf`, `.txt`, `.docx`
- Detects whether the document is legal, work-related, or personal
- Explains it in plain language, summarizes it, and flags anything risky or
  worth a second look
- Returns everything as one PDF report — nothing is written to disk or a
  database

## Architecture

\`\`\`
Upload → Extractor (pdf/txt/docx) → Analyzer (Azure OpenAI) → Report (PDF) → Response
\`\`\`

See [OVERVIEW.md](OVERVIEW.md) for the full technical breakdown, and
[docs/](docs/) for the change log and architecture decisions behind each piece.

## Development

\`\`\`bash
make test   # pytest
make lint   # ruff
\`\`\`

## Roadmap

Fase 2 (not in this MVP): OCR for scanned images, `.eml`/`.msg` email analysis
— both drop in as new `Extractor` implementations without touching the rest of
the pipeline.
```

- [ ] **Step 3: Write `OVERVIEW.md`**

```markdown
# Overview

## Pipeline

1. `ExtractorFactory` picks an `Extractor` (`PdfExtractor`, `TextExtractor`) by
   file extension.
2. The extractor returns `RawText` — plain extracted text plus the source
   filename. Extraction failures (corrupt file, empty/unreadable content) raise
   `ExtractionError`.
3. `DocumentAnalyzer` sends the text to Azure OpenAI with a system prompt that
   forces a JSON response, parsed into a Pydantic `AnalysisResult` (detected
   context, plain explanation, summary, red flags). A malformed response or a
   client-side failure after retries raises `AnalysisError`.
4. `ReportGenerator` renders `AnalysisResult` into an HTML template and
   converts it to PDF bytes via WeasyPrint (see
   [docs/adr/0001-pdf-generation-weasyprint.md](docs/adr/0001-pdf-generation-weasyprint.md)).
5. `DocumentAnalysisPipeline` wires the three stages together; `POST /analyze`
   maps their exceptions to HTTP status codes (415/422/502) and streams the
   PDF back on success.

## Statelessness

No component writes to disk or a database. Every stage operates on in-memory
bytes for the lifetime of one HTTP request.

## Testing

Every component is unit-tested in isolation; `DocumentAnalyzer` tests mock the
Azure OpenAI client entirely, so the suite never makes a real network call.
`tests/integration/` covers the full pipeline and the HTTP layer.

## Deployment

Local: Docker Compose (`make up`) or against a CI-published image (`make demo`).
Azure: Consumption-plan Azure Function fronting the same FastAPI app (ASGI),
deployed via Bicep for demo purposes and torn down afterward — see the Fase 2
infra work tracked separately from this MVP.
```

- [ ] **Step 4: Update `docker-compose.prebuilt.yml` with the real repository path**

Modify: replace `ghcr.io/OWNER/file-analyzer:latest` with the actual `ghcr.io/<your-github-username>/file-analyzer:latest` once the GitHub repo exists.

- [ ] **Step 5: Run the full test suite one last time**

Run: `pytest -v && ruff check src tests`
Expected: all tests PASS, lint clean

- [ ] **Step 6: Commit**

```bash
git add README.md OVERVIEW.md docs/adr docker-compose.prebuilt.yml
git commit -m "docs: add README, OVERVIEW, and ADR 0001; MVP complete"
```

- [ ] **Step 7: Create the GitHub repository and push**

This step requires your explicit go-ahead before running (creating/pushing to a
public GitHub repo is a visible, hard-to-fully-reverse action):

\`\`\`bash
gh repo create file-analyzer --public --source=. --remote=origin
git push -u origin master
\`\`\`

---

### Task 12: Azure Functions wrapper + Bicep infra (demo deploy)

**Files:**
- Create: `function_app.py`
- Create: `host.json`
- Create: `infra/main.bicep`
- Create: `infra/README.md`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `app` (Task 1, `src/api/main.py`) — wrapped as-is, no changes to the FastAPI app itself.

This task packages the existing FastAPI app to run on Azure Functions (Python v2,
ASGI) and provides a Bicep template to deploy it to a Consumption-plan Function
App for a demo, matching the roadmap's "zero fixed cost, tear-down after demo"
constraint. It requires the Azure Functions Core Tools to verify locally, and an
Azure subscription to actually deploy — the deploy/tear-down itself stays a
manual step you run when you want to record the demo, not part of CI.

- [ ] **Step 1: Add `azure-functions` to `requirements.txt`**

Modify `requirements.txt`, add this line at the end:

```
azure-functions==1.21.3
```

- [ ] **Step 2: Write `host.json`**

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

- [ ] **Step 3: Write `function_app.py`**

```python
import azure.functions as func

from src.api.main import app as fastapi_app

app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
```

- [ ] **Step 4: Verify locally with Azure Functions Core Tools**

Run: `pip install -r requirements.txt && func start`
Expected: the Functions host starts and logs a local URL (e.g.
`http://localhost:7071/api/health`); `curl http://localhost:7071/api/health`
returns `{"status":"ok"}`. If Azure Functions Core Tools isn't installed
locally, note that as a known gap and move on — this step doesn't block the
rest of the MVP, it only blocks the Azure demo deploy.

- [ ] **Step 5: Write `infra/main.bicep`**

```bicep
@description('Name prefix for all resources')
param namePrefix string = 'filean'

@description('Azure region')
param location string = resourceGroup().location

@secure()
@description('Azure OpenAI API key, injected as an app setting')
param azureOpenAiApiKey string

@description('Azure OpenAI endpoint URL')
param azureOpenAiEndpoint string

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string = 'gpt-4o-mini'

var storageAccountName = '${namePrefix}st${uniqueString(resourceGroup().id)}'
var functionAppName = '${namePrefix}-func-${uniqueString(resourceGroup().id)}'
var appServicePlanName = '${namePrefix}-plan'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
}

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      appSettings: [
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'AZURE_OPENAI_API_KEY', value: azureOpenAiApiKey }
        { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
        { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
        { name: 'AZURE_OPENAI_API_VERSION', value: '2024-08-01-preview' }
      ]
    }
  }
}

output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
```

- [ ] **Step 6: Write `infra/README.md`**

```markdown
# Infra (demo deploy)

Deploys the Function App for a live demo. Not part of CI — run manually, record
the demo, then tear down to keep costs at zero.

\`\`\`bash
az group create --name file-analyzer-demo --location westeurope

az deployment group create \
  --resource-group file-analyzer-demo \
  --template-file infra/main.bicep \
  --parameters azureOpenAiApiKey=<your-key> azureOpenAiEndpoint=<your-endpoint>

func azure functionapp publish <functionAppName-from-output>

# ... record the demo ...

az group delete --name file-analyzer-demo --yes --no-wait
\`\`\`
```

- [ ] **Step 7: Run the full test suite to confirm nothing broke**

Run: `pytest -v && ruff check src tests`
Expected: all tests PASS, lint clean (the Functions wrapper and Bicep files
don't affect the FastAPI app or its tests)

- [ ] **Step 8: Commit**

```bash
git add function_app.py host.json infra requirements.txt
git commit -m "feat: add Azure Functions wrapper and Bicep infra for demo deploy"
```

- [ ] **Step 9: Deploy for the demo, record it, then tear down**

This step costs real (if small) money and touches a real Azure subscription —
requires your explicit go-ahead before running, and should only run when
you're ready to record the demo:

Run the commands in `infra/README.md`. After recording, confirm the resource
group is deleted (`az group show --name file-analyzer-demo` should return
"not found").
