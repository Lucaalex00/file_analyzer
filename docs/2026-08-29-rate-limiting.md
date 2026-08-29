# 2026-08-29 — Rate limiting

## Context

Quarto item backend del lotto "ora" (priorità 3,
`docs/2026-08-28-fase2-roadmap.md`): l'endpoint pubblico non aveva alcuna
protezione contro l'abuso, e la sessione precedente aveva già discusso il
rischio (`slowapi` non era ancora una dipendenza del progetto).

## What changed

- `requirements.txt`: aggiunta `slowapi==0.1.9`.
- `src/api/config.py`: nuovo `Settings.rate_limit_per_minute` (env
  `RATE_LIMIT_PER_MINUTE`, default 20).
- `src/api/main.py`: `Limiter` di slowapi keyed sull'IP del client
  (`get_remote_address`), applicato a `/extract`, `/analyze`,
  `/analyze/review`, `/analyze/markdown` — non a `/health` o `/` (statici,
  nessun costo). Il limite è dinamico (letto da `Settings` a ogni
  richiesta, non fissato all'avvio), gestore `RateLimitExceeded` → 429.
  Ogni endpoint ha il proprio contatore indipendente (slowapi traccia per
  route + IP, non un budget condiviso).
- `tests/conftest.py` (nuovo): fixture `autouse` che chiama
  `limiter.reset()` prima di ogni test — necessario perché tutti i test di
  integrazione condividono la stessa istanza `app`/`TestClient`, altrimenti
  i contatori si accumulerebbero tra un test e l'altro.
- `.env.example`: documentata `RATE_LIMIT_PER_MINUTE`.

## Known gap

Lo storage del rate limit è in-memory (default di slowapi) — coerente col
vincolo "zero costo, nessun servizio esterno", ma significa che il limite
è per-processo: non tiene se in futuro il servizio girasse su più
istanze/repliche contemporaneamente (richiederebbe uno storage condiviso,
es. Redis).

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  84/84 test (4 nuovi: 2 su `rate_limit_per_minute` in `Settings`, 2 sul
  429 effettivo), 98.29% coverage, lint pulito.
- `npx playwright test` (via `make test-e2e`): 9/9 — confermato che il
  limite di default (20/minuto) non interferisce con l'uso normale della
  suite E2E.
