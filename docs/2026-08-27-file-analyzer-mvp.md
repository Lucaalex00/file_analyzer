# 2026-08-27 — File Analyzer MVP

## Context

People regularly receive documents they cannot read confidently — a lease, a
court notice, a work memo, a medical result — and have no cheap way to find out
what a document actually says and what in it deserves attention. The MVP builds
the smallest useful version of that: upload one file, get back a PDF report with
a plain-language explanation, a summary, and a list of red flags. Statelessness
is a product requirement, not just an implementation detail: no account, no
database, and the file lives only for the duration of the request.

Scope, sequencing, and constraints come from
[`2026-08-27-file-analyzer-design.md`](2026-08-27-file-analyzer-design.md) and
[`2026-08-27-file-analyzer-implementation-plan.md`](2026-08-27-file-analyzer-implementation-plan.md);
this entry summarizes the 12 implementation tasks plus the final whole-branch
review fixes.

## What changed

- **Extractors** — `Extractor` protocol returning `RawText`, with
  `TextExtractor` (`.txt`, `.docx`) and `PdfExtractor` (`pypdf`), selected by
  extension through `ExtractorFactory`. Unreadable or empty content raises
  `ExtractionError`; an unknown extension raises `UnsupportedFileTypeError`.
  Fase 2 extractors (OCR, email) drop in here without touching anything else.
- **Analyzer** — `DocumentAnalyzer` calls Azure OpenAI with a JSON-mode system
  prompt and validates the reply into a Pydantic `AnalysisResult` (detected
  context, plain explanation, summary, red flags). Transport failures get a
  small bounded retry; a malformed response fails fast. Document text sent to
  the model is hard-capped at `MAX_DOCUMENT_CHARS` (80k).
- **Report generator** — Jinja2 template rendered to PDF by WeasyPrint (see
  [`adr/0001-pdf-generation-weasyprint.md`](adr/0001-pdf-generation-weasyprint.md)),
  with autoescaping forced on since every rendered field originates from the
  LLM summarizing untrusted uploaded content.
- **Pipeline + API** — `DocumentAnalysisPipeline` wires extract → analyze →
  render; FastAPI exposes `GET /health` and `POST /analyze`, mapping domain
  errors to 413/415/422/502 and returning `application/pdf` on success.
- **Examples** — two sample input documents and
  `scripts/generate_examples.py`, which produces their reports on demand
  against real Azure OpenAI credentials.
- **CI/CD** — GitHub Actions workflow running ruff and pytest (with a coverage
  floor) on every PR, and publishing a container image to GHCR on `master`;
  `docker-compose.prebuilt.yml` + `make demo` run the published image with no
  local build.
- **Azure infra** — `function_app.py` ASGI wrapper, `host.json`, and
  `infra/main.bicep` (Linux Consumption Function App, storage, app settings)
  as a starting point for a throwaway demo deploy.
- **Docs** — `README.md` (quick start), `OVERVIEW.md` (technical breakdown),
  ADR 0001, `infra/README.md` (deploy steps plus the WeasyPrint caveat), and
  this change-log entry.

## Known gap

- **Fase 2, deliberately out of scope:** OCR for scanned images and
  `.eml`/`.msg` email analysis.
- **Two gated external steps not yet run**, pending explicit approval: the
  GitHub push (so the CI workflow has never executed, and the GHCR image
  `docker-compose.prebuilt.yml` refers to does not exist yet — its `OWNER`
  placeholder is filled in once the real repo does), and the Azure demo deploy.
- **The Consumption-plan deploy cannot run `/analyze` as written.** WeasyPrint
  needs Pango/Cairo/GDK-Pixbuf, which a Consumption plan gives no way to
  install; the real options are a containerized Function on Flex/Premium or the
  pure-Python `xhtml2pdf` fallback. Documented in `infra/README.md`.
- **Fixed in this final review pass:** Jinja2 autoescaping was silently off
  (the security fix above); CI triggered on `main` while the branch is
  `master`; `docker-compose.prebuilt.yml` did not reset the base file's
  `build`/`--reload`/source-mount; docs claimed checked-in example PDFs that do
  not exist; upload size was only checked after full buffering; no cap on
  document text sent to the LLM; the Azure OpenAI SDK's own timeout/retries
  compounded with the analyzer's; several Bicep defects (`reserved: true`,
  content-share settings, `httpsOnly`, hardcoded API version); CI never
  enforced coverage.
- **Left for later:** uploads between ~1MB and `MAX_FILE_SIZE_BYTES` still let
  Starlette spool the request body to an OS temp file — standard ASGI
  behavior, now documented honestly in `OVERVIEW.md` rather than worked around.
  Minor review findings not affecting correctness were also deferred.

## Verification

35/35 tests passing with 98% statement coverage, via the project's ephemeral
Docker container (local Python is 3.14, the app targets 3.12):

```bash
docker compose run --rm --no-deps -v "$(pwd):/app" -w /app api \
  sh -c "pip install --no-cache-dir -r requirements-dev.txt && pytest -v && ruff check src tests"
```

Lint clean. `docker compose -f docker-compose.yml -f docker-compose.prebuilt.yml config`
verified to merge to a build-free, mount-free, `--reload`-free service. The
Bicep template was not deployed or validated against a live subscription —
that step is gated behind separate approval.
