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

- Accepts `.pdf`, `.txt`, `.docx`
- Detects whether the document is legal, work-related, or personal
- Explains it in plain language, summarizes it, and flags anything risky or
  worth a second look
- Returns everything as one PDF report (or Markdown, via `POST /analyze/markdown`)
  — nothing is written to disk or a database

## Architecture

```
Upload → Extractor (pdf/txt/docx) → Analyzer (Azure OpenAI) → Report (PDF) → Response
```

See [OVERVIEW.md](OVERVIEW.md) for the full technical breakdown, and
[docs/](docs/) for the change log and architecture decisions behind each piece.

## Development

```bash
make test      # pytest
make lint      # ruff
make test-e2e  # Playwright, against the running stack (run `make up` first)
```

## Roadmap

Fase 2 (not in this MVP): OCR for scanned images, `.eml`/`.msg` email analysis
— both drop in as new `Extractor` implementations without touching the rest of
the pipeline.
