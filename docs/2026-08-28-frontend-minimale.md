# 2026-08-28 — Frontend minimale con preview

## Context

Secondo item del lotto "ora" del backlog Fase 2 (priorità 4, vedi
`docs/2026-08-28-fase2-roadmap.md` e `docs/2026-08-28-frontend-design.md`):
il progetto aveva solo un'API, nessuna interfaccia visiva.

## What changed

- `frontend/index.html`, `frontend/app.js`, `frontend/styles.css` (nuovi):
  HTML/CSS/JS vanilla, nessuna build step. Form con drag&drop + input file
  (limitato a `.pdf/.txt/.docx` lato client), stato "Analisi in corso...",
  gestione errori leggibile per status code (413/415/422/502/rete), e
  visualizzazione del PDF risultante inline via `<embed>` su un Object URL,
  più un link di download che usa il filename dall'header
  `Content-Disposition`.
- `src/api/main.py`: monta `/static` sulla cartella `frontend/` e serve
  `frontend/index.html` sulla root `/`. `/health` e `/analyze` invariati.
- `Dockerfile`: `COPY frontend/ frontend/`.
- `docker-compose.yml`: aggiunto il mount `./frontend:/app/frontend` per
  l'hot-reload in sviluppo.
- `e2e/`: infrastruttura Playwright (Node, non Python) — 3 test E2E contro
  il backend reale in Docker: form visibile in home, upload di un tipo file
  non supportato → messaggio d'errore leggibile (non JSON grezzo, path reale
  senza mock), upload con `/analyze` mockato (via `page.route`, dato che non
  abbiamo credenziali Azure OpenAI reali in questo ambiente) → PDF mostrato
  inline + link di download con filename corretto.
- `.github/workflows/ci.yml`: nuovo job `e2e` (avvia lo stack via
  `docker compose up`, aspetta `/health`, esegue Playwright); il job
  `docker` (pubblicazione GHCR) ora dipende anche da `e2e`, non solo da
  `test`.
- `Makefile`: nuovo target `test-e2e`.

## Known gap

Nessuna preview "prima/dopo" (testo estratto vs spiegazione) — è la feature
successiva del backlog, costruita sopra questa base.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`: 44/44
  test, 97.55% coverage, lint pulito (nessuna regressione dal backend
  esistente).
- `npx playwright test` (via `make test-e2e`, stack avviato con
  `docker compose up -d --build`): 3/3 test E2E passati.
- Verifica manuale: `curl http://localhost:8000/` e `/static/app.js`
  rispondono 200; pagina caricata in browser mostra correttamente form,
  drag&drop e — con `/analyze` mockato — preview PDF inline.
