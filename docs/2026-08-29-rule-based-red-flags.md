# 2026-08-29 — Pre-check red flag rule-based

## Context

Primo item backend del lotto "ora" (priorità 2, `docs/2026-08-28-fase2-roadmap.md`):
aumentare l'affidabilità della rilevazione dei red flag senza dipendere
esclusivamente dall'LLM.

## What changed

- `src/analyzer/rule_based_flags.py` (nuovo): `detect_rule_based_flags(text)` —
  un piccolo set di regole regex (rinnovo automatico, penale/recesso
  anticipato, scadenza espressa in giorni) che restituiscono `RedFlag` con
  `quote` uguale alla sottostringa esatta trovata nel testo (compatibile
  con l'evidenziazione già costruita per l'explainability).
- `src/pipeline.py`: `run_with_analysis()` ora unisce i red flag
  rule-based a quelli dell'LLM (deduplicati per titolo), dopo la chiamata
  ad `analyze()` e prima della generazione del report — nessuna chiamata
  aggiuntiva, nessun costo extra.

## Known gap

Il set di regole è volutamente piccolo (3 pattern IT/EN) — pensato come
complemento all'LLM, non sostituto. Espandibile in futuro senza toccare
il resto della pipeline.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  63/63 test (7 nuovi: 6 sul modulo regole, 1 sul merge nel pipeline),
  lint pulito.
