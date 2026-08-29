# 2026-08-29 — Batch upload

## Context

Sesto item backend del lotto "ora" (priorità 2,
`docs/2026-08-28-fase2-roadmap.md`): analizzare più file in una singola
richiesta, per uso reale oltre alla demo singolo-file.

## What changed

- `src/api/config.py`: nuovo `Settings.max_batch_files` (env
  `MAX_BATCH_FILES`, default 5).
- `src/api/main.py`: nuovo endpoint `POST /analyze/batch` (`files: list[UploadFile]`,
  `language`). Se il numero di file supera `max_batch_files` → 413 prima di
  processare qualunque file. Ogni file viene elaborato indipendentemente:
  se uno fallisce (415/422/502), il batch continua sugli altri — la
  risposta è sempre 200 con un array `results[]`, ciascuno
  `{"filename", "status": "ok"|"error", ...}` (con `analysis`/`pdf_base64`
  se ok, `status_code`/`detail` se errore).
- `.env.example`: documentata `MAX_BATCH_FILES`.

## Known gap

Nessuna UI frontend per il batch in questo giro (stesso approccio già
usato per `/analyze/markdown` e `/compare` — capacità API prima,
interfaccia dopo se richiesta). Il rate limiting conta la richiesta come
una sola chiamata, non per-file — un batch da 5 file consuma un solo
"credito" del limite per minuto, non cinque.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  99/99 test (6 nuovi: 2 su `max_batch_files`, 4 su `/analyze/batch`),
  lint pulito.
