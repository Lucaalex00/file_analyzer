# 2026-08-28 — Explainability (evidenziazione red flag nel testo)

## Context

Quinto e ultimo item del lotto "ora" lato frontend (priorità 2,
`docs/2026-08-28-fase2-roadmap.md`): mostrare *quali* passaggi del testo
originale hanno generato ogni red flag, non solo elencarli nel report PDF.

## What changed

- `src/analyzer/schemas.py`: `RedFlag` guadagna un campo `quote: str = ""`
  (default vuoto, retrocompatibile) — la citazione verbatim dal documento
  che ha fatto scattare quella red flag.
- `src/analyzer/prompts.py`: il prompt chiede esplicitamente al modello di
  includere `quote` come sottostringa esatta del documento (non
  parafrasata), così può essere ritrovata e evidenziata nel testo.
- `src/pipeline.py`: `DocumentAnalysisPipeline` guadagna
  `run_with_analysis()`, che restituisce sia l'`AnalysisResult` strutturato
  sia i byte del PDF in un'unica chiamata LLM; `run()` (usato da `/analyze`)
  ora è implementato sopra di esso, senza duplicare la chiamata al modello.
- `src/api/main.py`: nuovo endpoint `POST /analyze/review` — stessa
  pipeline di `/analyze`, ma risposta JSON
  `{"analysis": {...}, "pdf_base64": "..."}` invece del PDF grezzo.
  **Decisione deliberata**: `/analyze` resta invariato (contratto usato da
  curl/CLI/documentazione), il frontend passa a usare il nuovo endpoint —
  nessuna doppia chiamata LLM, nessuna rottura di retrocompatibilità.
- `frontend/filename.js` (nuovo): funzione pura `reportFilenameFor()` che
  replica lato client la sanificazione del filename già fatta server-side
  per `/analyze` (serve perché `/analyze/review` non porta più l'header
  `Content-Disposition`, essendo una risposta JSON).
- `frontend/app.js`: il submit ora chiama `/analyze/review`; il testo
  estratto già mostrato (dalla preview "prima/dopo") viene ri-renderizzato
  con i passaggi corrispondenti alle `quote` dei red flag avvolti in
  `<mark class="severity-...">`, con un tooltip (`title`) sul titolo della
  red flag.
- `frontend/styles.css`: stile per `mark.severity-high/medium/low` nel
  pannello del testo estratto.

## Known gap

L'evidenziazione è un semplice "trova e sostituisci" sulla stringa —
citazioni sovrapposte tra loro potrebbero produrre un annidamento non
pulito (limite accettato per l'MVP di questa feature). Nessun'altra
feature nota in sospeso per il lotto frontend: le prossime feature del
backlog sono lato backend (rule-based pre-check, export Markdown,
multi-lingua, rate limiting, ecc.).

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  56/56 test (7 nuovi: 3 sullo schema `quote`, 1 su `run_with_analysis`,
  4 su `/analyze/review`), 97.93% coverage, lint pulito.
- `node --test unit/**/*.test.js` (via `make test-frontend-unit`): 8/8
  (4 nuovi per `filename.js`).
- `npx playwright test` (via `make test-e2e`): 8/8 (1 nuovo per
  l'evidenziazione; i test esistenti aggiornati al nuovo contratto JSON di
  `/analyze/review`).
