# 2026-08-28 — Cronologia locale (localStorage)

## Context

Quarto item del lotto "ora" (priorità 2, `docs/2026-08-28-fase2-roadmap.md`):
tenere traccia delle analisi fatte in sessione, senza introdurre database o
persistenza lato server (vincolo di progetto invariato).

## What changed

- `frontend/history.js` (nuovo): modulo puro con `loadHistory(storage)` e
  `saveHistoryEntry(storage, entry, maxEntries)` — storage iniettato (non
  legge `window.localStorage` direttamente), così è testabile in Node senza
  un ambiente browser. Espone anche `STORAGE_KEY`. Pattern UMD minimale:
  utilizzabile sia come `<script>` globale (`FileAnalyzerHistory`) sia via
  `require()` nei test.
- `frontend/app.js`: dopo un'analisi riuscita, il PDF viene convertito in
  base64 (`FileReader`) e salvato come voce di cronologia (data, nome file
  originale, nome report, PDF in base64), fino a 10 voci (le più vecchie
  vengono scartate). Un pulsante "Riapri" per ogni voce ricostruisce il
  blob (`atob` + `Uint8Array`) e lo rimostra nel pannello report esistente.
- `frontend/index.html`/`styles.css`: nuova sezione "Cronologia" in fondo
  alla pagina.
- `e2e/unit/history.test.js` (nuovo): test unitari Node (`node --test`,
  nessuna dipendenza aggiuntiva) per `history.js` — nessuna voce iniziale,
  JSON corrotto gestito, ordine più-recente-primo, eviction oltre il limite.
- `e2e/tests/history.spec.js` (nuovo): 3 test Playwright — voce aggiunta
  dopo un'analisi, persistenza dopo reload della pagina, riapertura di una
  voce storica.
- `.github/workflows/ci.yml`: il job `e2e` ora esegue anche
  `npm run test:unit` prima dei test Playwright.
- `Makefile`: nuovo target `test-frontend-unit`.

## Known gap

Nessuna sincronizzazione tra dispositivi/browser (per design — è
esplicitamente locale, non lato server). Prossimo item del backlog:
explainability (evidenziare nel testo i passaggi dietro ogni red flag).

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  48/48 test, 97.75% coverage, lint pulito (nessuna modifica al backend
  Python in questa feature, solo verifica di non-regressione).
- `node --test unit/**/*.test.js` (via `make test-frontend-unit`): 4/4.
- `npx playwright test` (via `make test-e2e`): 7/7 (3 nuovi per la
  cronologia).
