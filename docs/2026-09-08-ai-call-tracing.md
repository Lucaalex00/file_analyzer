# 2026-09-08 — Tracing/logging delle chiamate AI

## Context

Secondo deliverable scelto dal blocco "AI Reliability" del piano personale
(`OBJECTIVE_v3.md`), esplicitamente richiesto: rendere osservabile ogni
chiamata all'LLM (durata, tentativi, esito), non solo "funziona/non
funziona". Come per il resto del blocco, costruito e verificato senza una
chiamata Azure OpenAI reale — usa lo stesso pattern di client finto già
presente nei test esistenti.

## Design

`src/observability/ai_tracing.py` (nuovo): `log_ai_attempt()`, una singola
funzione chiamata esplicitamente in ogni punto in cui `DocumentAnalyzer` e
`DocumentComparator` già distinguono gli esiti di un tentativo (successo,
errore di validazione che non fa ritentare, errore transitorio che fa
ritentare) — nessuna magia con decorator/context manager che indovina
l'esito dall'eccezione: il chiamante sa già cosa è successo, quindi lo
dichiara esplicitamente.

**Formato**, pensato per essere leggibile scorrendo i log a occhio, non solo
in un dashboard:

```
2026-09-08 17:42:03 [AI] document_analyzer | attempt 1/3 | transient_error | 812.4ms | error=RuntimeError
2026-09-08 17:42:04 [AI] document_analyzer | attempt 2/3 | success | 940.1ms
```

Ogni riga ha anche i campi strutturati corrispondenti (`ai_component`,
`ai_deployment`, `ai_attempt`, `ai_max_attempts`, `ai_outcome`,
`ai_duration_ms`, `ai_error_type`) via `extra=`, quindi resta
grep-abile/filtrabile anche se in futuro i log finiscono in un sistema
strutturato (es. Application Insights, quando il deploy Azure sarà attivo).

**Vincolo di privacy, non negoziabile**: dato che l'intera app si basa su
"nessun dato salvato, tutto in memoria per la durata della richiesta", i
log non devono mai contenere il contenuto del documento né il messaggio
grezzo dell'eccezione (che in alcune librerie client può includere pezzi
della richiesta che l'ha generato) — solo il nome della classe
dell'eccezione (`error_type`). Testato esplicitamente.

## What changed

- `src/observability/ai_tracing.py` (nuovo): `log_ai_attempt()`,
  `start_timer()`. Configura il proprio handler/livello sul logger
  `file_analyzer.ai` così i log INFO sono visibili anche in produzione
  (senza handler esplicito sarebbero silenziosamente scartati, dato che il
  root logger di default è a livello WARNING).
- `src/analyzer/document_analyzer.py` e `document_comparator.py`: ogni
  tentativo (successo, validation_error, transient_error) logga tramite
  `log_ai_attempt()`, stesso punto dove l'esito è già distinto dal codice
  esistente.
- `tests/unit/test_ai_tracing.py` (nuovo): formato del log, garanzia che
  il messaggio dell'errore non finisca mai nei log (solo il tipo).
- `tests/unit/test_document_analyzer.py`, `test_document_comparator.py`:
  nuovi test che verificano un record di log per tentativo, con l'esito
  corretto, e che il contenuto del documento non compaia mai nei log.

## Known gap

- Non ancora verificato in produzione/reale (la quota Azure OpenAI è
  ancora in attesa di approvazione) — solo verificato con client finti nei
  test. Da confermare visivamente su `docker logs` una volta sbloccata.
- Nessuna integrazione con un sistema di osservabilità esterno (Application
  Insights, ecc.) — resta un log testuale/strutturato locale, coerente con
  lo stato attuale del progetto (nessun deploy cloud ancora attivo).

## Verification

- Backend: 160/160 test passati (7 nuovi: 3 su `ai_tracing`, 3 su
  `document_analyzer` tracing, 1 su `document_comparator` tracing),
  97.46% coverage, `ruff check` pulito.
