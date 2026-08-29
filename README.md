# File Analyzer

Upload a document — a lease, a work memo, a personal letter — and get back a
plain-language explanation, a summary, and a list of things worth paying
attention to, as a downloadable PDF report. No account, no database, nothing
stored: the file exists only for the duration of the request.

## Quick start

```bash
git clone https://github.com/Lucaalex00/file_analyzer.git && cd file_analyzer
make env    # creates .env — fill in your Azure OpenAI credentials
make up     # builds and starts the API at http://localhost:8000
```

Then open http://localhost:8000 in a browser: drag a file in, click Analyze,
and the report shows up inline with a download link.

Or try it from the command line:

```bash
curl -F "file=@examples/sample_lease_contract.txt" http://localhost:8000/analyze -o report.pdf
```

See [`examples/`](examples/) for sample input files. Report PDFs are generated
on demand — run `python scripts/generate_examples.py` with your own Azure
OpenAI credentials (see [`examples/README.md`](examples/README.md)).

## What it does

- Accepts `.pdf`, `.txt`, `.docx`, `.eml` emails, and scanned images (`.png`,
  `.jpg`, `.jpeg`, `.tiff`, `.bmp` — via OCR, no cloud vision service needed)
- Detects whether the document is legal, work-related, or personal
- Explains it in plain language (choose it/en/fr/de/es), summarizes it, and
  flags anything risky or worth a second look — backed by both the LLM and a
  rule-based pre-check (auto-renewal, penalties, tight deadlines, phishing-style
  urgency/credential requests)
- Highlights each flagged passage back in the original text (explainability)
- Returns the analysis as a PDF report, as Markdown, or as structured JSON
- Compares two versions of a document and reports what changed
- Analyzes several files in one batch request
- Nothing is written to disk or a database — everything lives in memory for
  the duration of the request; the browser's local history (if you use the
  web UI) is the only thing that persists, and only in your own browser

## API

| Endpoint | Returns | Notes |
|---|---|---|
| `POST /extract` | `{"text": "..."}` | Extraction only, no LLM call |
| `POST /analyze` | PDF | The stable contract for curl/CLI consumers |
| `POST /analyze/review` | JSON (`analysis` + `pdf_base64`) | Used by the web UI |
| `POST /analyze/markdown` | Markdown file | |
| `POST /analyze/batch` | JSON (`results[]`, one per file) | |
| `POST /compare` | JSON (`comparison`) | Takes `file_a` + `file_b` |

All of the above accept an optional `language` field (`it` default) and are
rate-limited per client IP (`RATE_LIMIT_PER_MINUTE`, default 20/minute).

## CLI

The same pipeline also runs without a server, via `src/cli.py`:

```bash
docker compose run --rm api python -m src.cli extract examples/sample_lease_contract.txt
docker compose run --rm api python -m src.cli analyze examples/sample_lease_contract.txt --format markdown
docker compose run --rm api python -m src.cli compare v1.txt v2.txt
```

`extract` never calls the LLM; `analyze` and `compare` need
`AZURE_OPENAI_ENDPOINT`/`AZURE_OPENAI_API_KEY` set (same `.env` as the API).

## Architecture

```
Upload → Extractor (pdf/txt/docx/eml/image via OCR) → Analyzer (Azure OpenAI + rule-based) → Report (PDF/Markdown) → Response
```

See [OVERVIEW.md](OVERVIEW.md) for the full technical breakdown, and
[docs/](docs/) for the change log and architecture decisions behind each piece.

## Development

```bash
make test               # pytest
make lint                # ruff
make test-e2e            # Playwright, against the running stack (run `make up` first)
make test-frontend-unit  # Node's built-in test runner, no running stack needed
```

## Roadmap

Not yet built: `.msg` (Outlook binary format) email support — `.eml` is
covered — custom PDF branding/themes, and a real Azure Functions deploy
(Bicep already in `infra/`, gated behind a manual, explicitly-approved
step).
