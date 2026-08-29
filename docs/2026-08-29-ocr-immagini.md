# 2026-08-29 — Estrattore OCR per immagini

## Context

Fase 2 originale del progetto (vedi `docs/2026-08-27-file-analyzer-design.md`):
supporto a immagini scansionate. Implementato via Tesseract locale (non Azure
AI Vision) per restare a costo zero, coerente col resto del progetto.

## What changed

- `src/extractors/image_extractor.py` (nuovo): `ImageExtractor` — apre
  l'immagine con Pillow, esegue l'OCR con `pytesseract`, solleva
  `ExtractionError` se l'immagine è corrotta o se non viene riconosciuto
  alcun testo. Estensioni supportate: `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`.
- `src/extractors/factory.py`: `ExtractorFactory` registra `ImageExtractor`
  di default (dopo `PdfExtractor`/`TextExtractor`).
- `requirements.txt`: `pytesseract==0.3.13`, `Pillow==12.3.0` (esplicito,
  prima arrivava solo transitivamente da WeasyPrint).
- `Dockerfile` e `.github/workflows/ci.yml`: aggiunto il pacchetto di sistema
  `tesseract-ocr`.
- `frontend/index.html`: l'input file e il testo del dropzone ora accettano
  anche le estensioni immagine.
- `README.md`/`OVERVIEW.md`: aggiornati per riflettere il supporto OCR (la
  sezione "Roadmap" del README non lo elenca più come mancante).

## Known gap

Nessuna lingua OCR configurata esplicitamente — Tesseract usa il pacchetto
linguistico di default installato (`eng` su Debian). Documenti scansionati
in altre lingue potrebbero avere una qualità di riconoscimento inferiore;
non affrontato in questo giro.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  106/106 test (7 nuovi: 6 su `ImageExtractor` — incluso un test reale con
  OCR su un'immagine generata al volo con testo disegnato — 1 sulla
  registrazione in `ExtractorFactory`), 99.26% coverage, lint pulito.
- `npx playwright test` (via `make test-e2e`): 9/9, nessuna regressione.
