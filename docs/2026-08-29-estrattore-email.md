# 2026-08-29 — Estrattore email (.eml) + pre-check phishing

## Context

Ultima parte del gap Fase 2 originale insieme all'OCR (vedi
`docs/2026-08-27-file-analyzer-design.md`): analisi di email con red flag
specifiche.

## What changed

- `src/extractors/email_extractor.py` (nuovo): `EmailExtractor` per `.eml`,
  usa il modulo standard `email` di Python (nessuna dipendenza aggiuntiva).
  Estrae subject/from/to + corpo (preferendo `text/plain`, fallback
  `text/html`); solleva `ExtractionError` se il parsing fallisce o il corpo
  è vuoto.
- `src/extractors/factory.py`: `ExtractorFactory` registra `EmailExtractor`.
- `src/analyzer/rule_based_flags.py`: nuova regola "Possibile phishing"
  (linguaggio di urgenza + richiesta di credenziali/verifica account, IT+EN)
  — si applica a qualunque testo, particolarmente utile per le email.
- `frontend/index.html`: input file e testo del dropzone accettano anche
  `.eml`.
- `README.md`: aggiornato (`.eml` non più elencato come mancante; resta
  `.msg`, formato binario Outlook, esplicitamente fuori scope).

## Known gap

`.msg` (formato binario proprietario di Outlook) non è supportato —
richiederebbe una libreria aggiuntiva (`extract-msg` o simili) con più
complessità/edge case; rimandato, documentato esplicitamente nel README.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  113/113 test (7 nuovi: 5 su `EmailExtractor`, 1 sulla registrazione in
  factory, 1 sulla regola phishing), 98.82% coverage, lint pulito.
- `npx playwright test` (via `make test-e2e`): 9/9, nessuna regressione.
