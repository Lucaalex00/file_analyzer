# 2026-08-28 — Preview "prima/dopo"

## Context

Terzo item del lotto "ora" (priorità 3, `docs/2026-08-28-fase2-roadmap.md`):
mostrare il testo estratto grezzo accanto al report finale, invece del solo
PDF alla fine del flusso.

## What changed

- `src/api/main.py`: nuovo endpoint `POST /extract` — fa solo estrazione
  testo (`ExtractorFactory`/`Extractor.extract`), **nessuna chiamata Azure
  OpenAI**, per evitare di raddoppiare il costo/tempo dell'LLM solo per una
  preview. Stessa mappatura errori di `/analyze` (415/422/413), risposta
  `{"text": "..."}`. Il controllo dimensione file è stato estratto in un
  helper condiviso (`_read_within_size_limit`) usato da entrambi gli
  endpoint.
- `src/api/dependencies.py`: nuova dependency `get_extractor_factory()`
  (cache-ata), separata da `get_pipeline()` — l'endpoint `/extract` non ha
  bisogno di credenziali Azure OpenAI per funzionare.
- `frontend/index.html`/`app.js`/`styles.css`: alla selezione del file
  (change o drop, prima ancora di inviare il form), il frontend chiama
  `/extract` e mostra il testo grezzo in un pannello "Testo estratto" a
  fianco del pannello "Report" (layout a due colonne, single-column sotto
  gli 800px). Se `/extract` fallisce, il pannello resta semplicemente
  nascosto — l'errore definitivo emerge comunque quando l'utente clicca
  "Analizza".

## Known gap

Nessuno noto per questa feature specifica. Prossimo item del backlog:
cronologia locale (localStorage).

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  48/48 test (4 nuovi per `/extract`), 97.75% coverage, lint pulito.
- `npx playwright test` (via `make test-e2e`): 4/4 test E2E (1 nuovo,
  verifica reale contro `/extract` — nessun mock, dato che non tocca l'LLM).
