# Overview

## Pipeline

1. `ExtractorFactory` picks an `Extractor` (`PdfExtractor`, `TextExtractor`,
   `ImageExtractor`) by file extension. `ImageExtractor` runs Tesseract OCR
   locally (via `pytesseract`) — no cloud vision service, no extra cost.
2. The extractor returns `RawText` — plain extracted text plus the source
   filename. Extraction failures (corrupt file, empty/unreadable content, no
   text recognized in an image) raise `ExtractionError`.
3. `DocumentAnalyzer` sends the text to Azure OpenAI with a system prompt that
   forces a JSON response, parsed into a Pydantic `AnalysisResult` (detected
   context, plain explanation, summary, red flags, each translated into the
   requested `language`). A malformed response or a client-side failure after
   retries raises `AnalysisError`. `src/analyzer/rule_based_flags.py` adds a
   second, independent pass (regex-based, no LLM call) whose results are
   merged in — a document is never left with zero flags just because the
   model missed something a simple pattern would have caught.
4. `ReportGenerator` renders `AnalysisResult` into an HTML template and
   converts it to PDF bytes via WeasyPrint (see
   [docs/adr/0001-pdf-generation-weasyprint.md](docs/adr/0001-pdf-generation-weasyprint.md)).
5. `DocumentAnalysisPipeline` wires the three stages together. `POST /analyze`
   maps their exceptions to HTTP status codes (415/422/502) and returns the
   PDF directly — the contract curl/CLI consumers rely on. `POST /analyze/review`
   runs the same pipeline (`run_with_analysis`, one LLM call, no duplicated
   cost) but returns JSON (`{"analysis": {...}, "pdf_base64": "..."}`) instead
   — used by the frontend, which needs the structured `red_flags` (each with a
   verbatim `quote` from the source text) to highlight them back in the
   extracted-text preview, something a raw PDF response can't carry.
   `POST /extract` runs extraction only (no LLM call) so the frontend can show
   the raw text as soon as a file is selected, before the user even submits.

## Statelessness

The application itself writes nothing to disk or to a database: every stage
operates on in-memory bytes for the lifetime of one HTTP request. Note that for
uploads over ~1MB, Starlette's `UploadFile` may spool the request body to an OS
temp file for the duration of the request (standard ASGI behavior), cleaned up
automatically when the request completes. `POST /analyze` rejects oversized
uploads from `Content-Length` before reading the body where the client provides
it, with a post-read size check as a fallback.

## Demo mode

`Settings.is_demo_mode` is `True` whenever `AZURE_OPENAI_ENDPOINT`/
`AZURE_OPENAI_API_KEY` aren't set. In that case `src/api/dependencies.py`
wires in `DemoAIClient` (`src/analyzer/demo_client.py`) instead of a real
`AzureOpenAI` client — it duck-types the same `client.chat.completions.create(...)`
surface, so `DocumentAnalyzer`/`DocumentComparator` need no changes at all to
support it. Red flags stay real: `DemoAIClient` runs the same
`detect_rule_based_flags()` against the actual extracted text; only the
narrative explanation/comparison is templated, and it always says so
explicitly — in the API response, a startup log warning, `/health`'s
`demo_mode` field, and a banner in the UI. This is what makes
`docker run ghcr.io/.../file_analyzer:latest` usable with zero setup: the
whole pipeline runs for real except the AI-written prose.

## PDF table reconstruction

When `PdfExtractor`'s primary text layer looks corrupted (`_looks_corrupted()`
in `src/extractors/pdf_extractor.py` — density of spaces, or a density of
lowercase-to-uppercase letter transitions with no space between them, both
signals of a broken embedded font encoding), it falls back to OCR. If
`pdfplumber` detects real vector-drawn table lines on the page, each table is
reconstructed cell-by-cell (`_reconstruct_table_as_grid`) — every cell OCR'd
individually rather than the whole page as one blob, which is both far more
accurate and immune to the broken text encoding (OCR reads pixels, not the
PDF's internal character mapping). Content above the topmost table (header)
is OCR'd as one block; content below the lowest table is never discarded —
financial/legal documents can't risk losing something that might matter — it's
kept in its own clearly labelled section instead.

## AI reliability

Three defenses, none of which need a live LLM call to build or verify
(fake/mocked clients throughout, see `tests/eval/`):

- **Prompt injection defenses**: `SYSTEM_PROMPT`/`COMPARISON_SYSTEM_PROMPT`
  wrap document content in `<document>`/`<version_a>`/`<version_b>` tags and
  instruct the model to treat it as untrusted data, never as instructions. A
  rule-based detector (same mechanism as the other red-flag rules) also
  flags injection-style phrases ("ignore previous instructions") as a
  visible red flag — defense in depth, not a silent block.
- **Call tracing**: `src/observability/ai_tracing.py` logs every LLM call
  attempt (component, attempt number, outcome, duration) — never the
  document content or the raw exception message, only the exception's class
  name, consistent with the app's "nothing is stored" premise.
- **Eval/regression suite** (`tests/eval/test_analysis_regression.py`): a
  small set of representative documents run through the whole pipeline with
  a fixed fake LLM response, asserting the rule-based layer catches red
  flags the model misses — guards against a future change silently
  weakening the merge logic or the injection defense.

## Testing

Every component is unit-tested in isolation; `DocumentAnalyzer` tests mock the
Azure OpenAI client entirely, so the suite never makes a real network call.
`tests/integration/` covers the full pipeline and the HTTP layer;
`tests/eval/` covers pipeline-wide behavior against fixed fake responses.

## Deployment

Local: Docker Compose (`make up` for local dev, `make demo` or
`docker compose -f docker-compose.yml -f docker-compose.prebuilt.yml up -d`
against the CI-published image — same Compose project either way, so
switching between them never leaves a duplicate container behind). No
`.env` is required to start: with no Azure OpenAI credentials the app runs
in demo mode (see above) instead of failing to start.

Azure: **Azure Container Apps**, deployed via Bicep (`infra/main.bicep`) —
live at the URL in the README's "Live demo" section. The original plan
targeted a Consumption-plan Azure Function, which never actually worked:
that plan gives no way to install the system libraries (Pango, Cairo,
GDK-Pixbuf) WeasyPrint needs, so `/health` would come up while `/analyze`
failed at import or render time. Container Apps runs the project's own
`Dockerfile` unmodified instead. Log Analytics + a Container Apps managed
environment capture container logs; the app scales to zero when idle, so
cost stays near zero on the always-free monthly grant. No Azure OpenAI
credentials are attached to the live deploy — it runs in demo mode.
