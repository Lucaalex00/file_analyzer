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

## Testing

Every component is unit-tested in isolation; `DocumentAnalyzer` tests mock the
Azure OpenAI client entirely, so the suite never makes a real network call.
`tests/integration/` covers the full pipeline and the HTTP layer.

## Deployment

Local: Docker Compose (`make up`) or against a CI-published image (`make demo`).
Azure: Consumption-plan Azure Function fronting the same FastAPI app (ASGI),
deployed via Bicep for demo purposes and torn down afterward — see the Fase 2
infra work tracked separately from this MVP.
