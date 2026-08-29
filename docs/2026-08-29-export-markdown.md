# 2026-08-29 — Export anche in Markdown

## Context

Secondo item backend del lotto "ora" (priorità 2,
`docs/2026-08-28-fase2-roadmap.md`): oltre al PDF, poter scaricare l'analisi
anche come file Markdown — utile per un futuro consumer CLI e per chi vuole
un formato più leggero/versionabile.

## What changed

- `src/report/templates/report.md.j2` (nuovo): stesso contenuto del template
  HTML (contesto, riassunto, spiegazione, red flag con citazione), reso in
  Markdown. Usa lo stesso `Environment` Jinja2 con `autoescape=True` già in
  uso per l'HTML — l'escaping serve anche qui, dato che i renderer Markdown
  (es. GitHub) eseguono l'HTML incorporato.
- `src/report/report_generator.py`: nuovo metodo `generate_markdown()`.
- `src/pipeline.py`: `DocumentAnalysisPipeline.render_markdown()` — riusa
  l'`AnalysisResult` già calcolato da `run_with_analysis()`, nessuna chiamata
  LLM aggiuntiva se già disponibile un'analisi.
- `src/api/main.py`: nuovo endpoint `POST /analyze/markdown` (stessa mappatura
  errori di `/analyze`), restituisce `text/markdown` con
  `Content-Disposition` (`<stem>-report.md`). Chiamata indipendente da
  `/analyze`/`/analyze/review` — comporta una propria chiamata LLM se usato
  da solo (stesso modello di costo di `/analyze`).
- `frontend/`: pulsante "Scarica anche in Markdown" accanto al download PDF
  — richiama `/analyze/markdown` con lo stesso file già analizzato
  (chiamata LLM aggiuntiva solo se l'utente clicca esplicitamente il
  pulsante, azione opzionale).

## Known gap

Riaprire una voce di cronologia non permette di riesportare in Markdown
(il file originale non è conservato in `localStorage`, solo il PDF) — il
pulsante resta nascosto in quel caso.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  71/71 test (8 nuovi: 3 su `generate_markdown`, 1 su
  `pipeline.render_markdown`, 4 su `/analyze/markdown`), 98.19% coverage,
  lint pulito.
- `npx playwright test` (via `make test-e2e`): 9/9 (1 nuovo, verifica il
  download del file `.md` con `page.waitForEvent("download")`).
