# 2026-08-29 — CLI standalone

## Context

Penultimo item del lotto "ora" (priorità 2, `docs/2026-08-28-fase2-roadmap.md`):
un secondo entry point per un pubblico tecnico, senza passare dal server.

## What changed

- `src/cli.py` (nuovo): tre sottocomandi via `argparse`
  (`python -m src.cli ...`):
  - `extract <file>` — solo estrazione testo, nessuna chiamata LLM, stampa
    su stdout.
  - `analyze <file> [--language it] [--format pdf|markdown] [--output path]`
    — riusa `DocumentAnalysisPipeline` (stessa pipeline dell'API), scrive
    il report su file (default: `<nomefile>.report.pdf`/`.report.md`).
  - `compare <file_a> <file_b> [--language it]` — stampa il confronto come
    JSON su stdout.
  Le funzioni `run_extract`/`run_analyze`/`run_compare` accettano
  factory/pipeline/comparator come parametri (dependency injection), così
  sono testabili con dei fake senza toccare Azure OpenAI; `main()` è
  l'unico punto che costruisce le dipendenze reali.
- `README.md`: nuova sezione "CLI" con esempi d'uso via
  `docker compose run`; aggiornata la roadmap (CLI non più tra le cose
  mancanti).

## Known gap

Nessun packaging come comando installabile (`pip install` + entry point
console) — si usa sempre come modulo (`python -m src.cli`), coerente con
l'assenza di build/packaging altrove nel progetto.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  122/122 test (9 nuovi sul modulo CLI), lint pulito.
- Verifica manuale: `docker compose run --rm api python -m src.cli extract
  examples/sample_lease_contract.txt` stampa correttamente il testo
  estratto dal file di esempio (percorso reale end-to-end, non mockato).
