# 2026-08-28 — Hardening pack

## Context

Primo elemento del backlog Fase 2 (priorità 4, vedi
`docs/2026-08-28-fase2-roadmap.md`): un lotto di correzioni a basso rischio e
alto valore, per lo più già individuate come minor nella code review finale
dell'MVP, prima di aggiungere nuova superficie applicativa.

## What changed

- `src/api/main.py`: la risposta di `POST /analyze` ora include l'header
  `Content-Disposition: attachment; filename="<nome-sanificato>-report.pdf"`.
  Il filename originale viene ridotto al solo nome file (niente componenti di
  percorso, utile contro path traversal) e sanificato sostituendo ogni
  carattere non alfanumerico/`.`/`-`/`_` con `_`.
- `src/api/main.py`: aggiunto un `lifespan` FastAPI che chiama
  `Settings.validate()` all'avvio dell'applicazione — se mancano
  `AZURE_OPENAI_ENDPOINT`/`AZURE_OPENAI_API_KEY` il processo fallisce subito
  con un errore chiaro, invece di un 500 anonimo alla prima richiesta reale.
- `src/api/config.py`: `MAX_FILE_SIZE_BYTES=""` (stringa vuota, comune in
  alcuni `.env`) non fa più crashare `int()` — ricade sul default; nuovo
  metodo `Settings.validate()`.
- `.dockerignore` (nuovo): esclude `.git/`, `tests/`, `docs/`, `examples/`,
  `infra/`, cache varie e `.env` dal contesto di build.
- `Dockerfile`: il container ora gira come utente non-root (`appuser`);
  aggiunta una direttiva `HEALTHCHECK` verso `/health` (via `urllib`, senza
  installare `curl`).

## Known gap

Le direttive Docker (utente non-root, healthcheck) non sono coperte da
pytest — verificate manualmente con `docker compose up` + `docker compose
exec api whoami` (→ `appuser`) e `docker inspect --format='{{.State.Health.Status}}'`
(→ `healthy`).

## Verification

- `pytest --cov=src --cov-fail-under=80 -v`: 44/44 test passati (7 nuovi:
  2 su Content-Disposition/sanificazione filename, 2 su lifespan/validazione
  config, 5 su `Settings`), coverage 97.98%.
- `ruff check src tests`: pulito.
- Verifica manuale Docker: build ok, container avviato come `appuser`,
  `docker inspect` conferma stato `healthy` dopo lo start-period.
