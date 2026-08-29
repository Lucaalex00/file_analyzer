# 2026-08-29 — Spiegazione multi-lingua

## Context

Terzo item backend del lotto "ora" (priorità 3, `docs/2026-08-28-fase2-roadmap.md`):
poter scegliere la lingua della spiegazione, non fissa a inglese/italiano.

## What changed

- `src/analyzer/prompts.py`: `build_user_prompt(document_text, language="it")`
  aggiunge un'istruzione esplicita al prompt utente — solo
  `plain_explanation`, `summary` e i campi testuali di ogni red flag vanno
  tradotti; `detected_context`, `severity` e `quote` restano invariati
  (`quote` deve restare verbatim nella lingua originale del documento, per
  continuare a funzionare con l'evidenziazione).
- `src/analyzer/document_analyzer.py`: `DocumentAnalyzer.analyze()` accetta
  `language: str = "it"` e lo propaga al prompt.
- `src/pipeline.py`: `run()`/`run_with_analysis()` accettano e propagano
  `language`.
- `src/api/main.py`: `/analyze`, `/analyze/review`, `/analyze/markdown`
  accettano un campo form `language` (default `"it"`).
- `frontend/`: menu a tendina "Lingua della spiegazione" (it/en/fr/de/es),
  incluso nella richiesta a `/analyze/review` e `/analyze/markdown`.

## Bug trovato e corretto in corsa

Durante la verifica E2E è emersa una race condition reale (non solo un test
flaky): l'evidenziazione dei red flag nel testo estratto dipende dal
completamento della chiamata `/extract` fatta alla selezione del file: se
`/analyze/review` risponde prima che `/extract` sia terminata,
`lastExtractedText` potrebbe essere ancora vuota. `frontend/app.js` ora
tiene traccia della promise di `/extract` e la attende esplicitamente prima
di applicare l'evidenziazione — bug pre-esistente (introdotto con la
feature explainability), scoperto solo ora sotto il carico dei test E2E in
parallelo.

## Known gap

Nessuna rilevazione automatica della lingua del documento — la scelta è
sempre esplicita dell'utente (default italiano).

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  80/80 test (9 nuovi: 3 sul prompt, 1 sull'analyzer, 1 sul pipeline,
  4 sui tre endpoint), 98.21% coverage, lint pulito.
- `npx playwright test --repeat-each=3` (via `make test-e2e`): 27/27 (9
  test × 3 ripetizioni) — verifica esplicita che la fix alla race
  condition regga sotto stress.
