# 2026-08-29 — Confronto tra due versioni di un documento

## Context

Quinto item backend del lotto "ora" (priorità 2,
`docs/2026-08-28-fase2-roadmap.md`): confrontare due versioni di un
documento (es. contratto v1 vs v2) e ottenere cosa è cambiato.

## What changed

- `src/analyzer/comparison_schemas.py` (nuovo): `Difference`
  (`title`, `description`, `change_type: added|removed|modified`),
  `ComparisonResult` (`summary`, `differences`).
- `src/analyzer/comparison_prompts.py` (nuovo): prompt dedicato al
  confronto, riusa `LANGUAGE_NAMES`/`MAX_DOCUMENT_CHARS` da
  `prompts.py` (promosso da privato a pubblico per essere condiviso).
- `src/analyzer/document_comparator.py` (nuovo): `DocumentComparator`,
  stessa logica di retry di `DocumentAnalyzer` ma per il confronto
  (`ComparisonError` invece di `AnalysisError`).
- `src/api/dependencies.py`: estratto `_build_azure_client()` (riusato ora
  da `get_document_analyzer()`, `get_document_comparator()`,
  `get_pipeline()` — un solo punto di costruzione del client Azure OpenAI).
- `src/api/main.py`: nuovo endpoint `POST /compare` (`file_a`, `file_b`,
  `language`) — estrae il testo da entrambi i file (stesso
  `ExtractorFactory`), chiama il comparatore, risponde con JSON
  `{"comparison": {...}}`. Stessa mappatura errori degli altri endpoint
  (415/422/502) più rate limiting.

## Known gap

Nessuna UI frontend per questa feature in questo giro — è pensata come
capacità API, sullo stesso modello di `/analyze/markdown`. Se serve
un'interfaccia visiva, è un item separato del backlog.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  93/93 test (9 nuovi: 4 su `DocumentComparator`, 5 su `/compare`), lint
  pulito.
