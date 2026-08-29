# 2026-08-29 — Branding/temi personalizzabili del PDF

## Context

Ultimo item del lotto "ora" (priorità 1, `docs/2026-08-28-fase2-roadmap.md`):
poter personalizzare nome e colore del report senza toccare il codice.

## What changed

- `src/report/report_generator.py`: `ReportGenerator.__init__` accetta ora
  `brand_name` (default `"File Analyzer"`) e `accent_color` (default
  `"#2563eb"`, lo stesso blu già usato nel frontend), passati al rendering
  sia HTML sia Markdown.
- `src/report/templates/report.html.j2`: riga di brand in alto, colore
  d'accento usato per i bordi degli `<h2>` (prima hardcoded).
- `src/report/templates/report.md.j2`: riga di brand in corsivo in cima.
- `src/api/config.py`: `Settings.report_brand_name`/`report_accent_color`
  (env `REPORT_BRAND_NAME`/`REPORT_ACCENT_COLOR`).
- `src/api/dependencies.py`: nuova `get_report_generator()`, usata da
  `get_pipeline()` — costruisce il `ReportGenerator` con i valori da
  `Settings` invece dei default hardcoded.
- `.env.example`: documentate le due nuove variabili.

## Known gap

Nessun logo/immagine personalizzabile (solo nome testuale + colore) — un
logo richiederebbe gestione upload/storage di un asset, fuori scope per
questo giro vista la natura stateless del progetto.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  127/127 test (6 nuovi: 2 su `Settings`, 4 su `ReportGenerator`), 96.89%
  coverage, lint pulito.
- `npx playwright test` (via `make test-e2e`): 9/9, nessuna regressione.
