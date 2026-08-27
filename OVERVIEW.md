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
