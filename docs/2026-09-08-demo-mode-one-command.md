# 2026-09-08 — Modalità demo automatica, avvio a un comando

## Context

Obiettivo esplicito dell'utente: un recruiter (o chiunque) deve poter
provare l'intera applicazione con **un solo comando Docker**, senza
clonare il repo, senza configurare `.env`, senza avere credenziali Azure
OpenAI. Utile anche a noi stessi in questo momento, dato che la quota
Azure OpenAI è ancora in attesa di approvazione.

Prima di oggi, l'avvio falliva del tutto senza credenziali: `Settings.validate()`
sollevava un'eccezione all'avvio (`lifespan()` in `main.py`), quindi
l'intero container non partiva senza un `.env` valido con
`AZURE_OPENAI_ENDPOINT`/`AZURE_OPENAI_API_KEY` reali.

## Design

**Modalità demo automatica** (scelta: automatica quando mancano le
credenziali, non un flag esplicito — per la massima comodità di chi prova
l'app per la prima volta):

- `Settings.is_demo_mode` (nuova property): `True` quando endpoint o
  chiave Azure OpenAI sono vuoti.
- `src/analyzer/demo_client.py` (nuovo): `DemoAIClient`, un client finto
  che duck-types la stessa superficie (`client.chat.completions.create(...)`)
  del vero `AzureOpenAI`, quindi è una sostituzione trasparente per
  `DocumentAnalyzer`/`DocumentComparator` — nessuna modifica a quelle
  classi. I red flag restano **reali**: `DemoAIClient` richiama lo stesso
  `detect_rule_based_flags()` già usato in produzione sul testo
  effettivamente estratto. Solo la spiegazione narrativa è templata, e lo
  dichiara sempre esplicitamente ("[Modalità demo] ... questa spiegazione
  è simulata, non generata da un vero modello AI").
- `src/api/dependencies.py`: `_build_ai_client()` sceglie `DemoAIClient()`
  o il vero `AzureOpenAI` in base a `settings.is_demo_mode` — un solo
  punto di decisione, nessun altro file tocca la differenza.
- **Mai silenziosamente fuorviante**: la modalità demo è segnalata su tre
  livelli — log di avvio (`logger.warning(...)`), campo `demo_mode` in
  `/health`, e un banner visibile nell'interfaccia (tradotto in tutte le
  5 lingue) che il frontend mostra leggendo `/health` al caricamento.

**Avvio a un comando**: `docker-compose.yml` non richiede più
`env_file: .env` (che rendeva il file obbligatorio) — sostituito con un
blocco `environment:` con default vuoti via `${VAR:-}`. Il comando finale
per chiunque, zero configurazione:

```
docker run -d -p 8000:8000 ghcr.io/lucaalex00/file_analyzer:latest
```

L'immagine è già pubblicata automaticamente su GHCR a ogni push su
master dal job `docker` della pipeline CI esistente — non serve nessuna
modifica lì.

## What changed

- `src/api/config.py`: rimosso `validate()` (nessuna impostazione è più
  "obbligatoria" — mancare le credenziali Azure ora significa demo mode,
  non un errore), aggiunta `is_demo_mode`.
- `src/analyzer/demo_client.py` (nuovo): `DemoAIClient`.
- `src/api/dependencies.py`: `_build_azure_client()` rinominato
  `_build_ai_client()`, sceglie demo o reale in base a `is_demo_mode`.
- `src/api/main.py`: `lifespan()` non solleva più eccezioni per
  credenziali mancanti, logga un warning in modalità demo; `/health` ora
  include `demo_mode`.
- `docker-compose.yml`, `docker-compose.prebuilt.yml`: `.env` non più
  obbligatorio.
- `.env.example`: valori Azure OpenAI ora vuoti di default (prima erano
  placeholder non vuoti tipo `replace-me`, che avrebbero disattivato la
  modalità demo per errore anche senza credenziali vere).
- `frontend/index.html`, `app.js`, `styles.css`, `i18n.js`: banner
  "modalità demo" mostrato/nascosto in base a `/health`, tradotto in
  it/en/fr/de/es.
- `README.md`: nuovo Quick Start con `docker run` come comando principale.
- `Makefile`: aggiornata la descrizione di `make demo`.

## Known gap

- La regola "Rinnovo automatico" (`rule_based_flags.py`) non intercetta
  l'ordine "automatically renews" (solo "renews automatically") — scoperto
  testando la modalità demo sul cedolino di esempio del lease, dove il
  testo dice "automatically renews". Non è stato toccato in questo lavoro
  (fuori scope), ma incide sulla qualità percepita della demo — candidato
  per un fix futuro separato.
- Il banner demo dipende dal fetch di `/health` al caricamento pagina: se
  quella richiesta fallisce silenziosamente (rete lenta, ecc.) il banner
  semplicemente non appare, senza errore visibile — accettabile per un
  banner informativo non bloccante.

## Verification

- Backend: 171/171 test passati (nuovi test su `is_demo_mode`,
  `DemoAIClient`, wiring in `dependencies.py`, `/health`, avvio senza
  credenziali), 97.53% coverage, `ruff check` pulito.
- Playwright e2e: 18/18 test passati (nuovi test sul banner demo mode).
- Verificato manualmente end-to-end: `.env` rimosso, `docker compose up
  --build` senza alcuna configurazione, richiesta reale (non mockata) a
  `/analyze/review` con `examples/sample_lease_contract.txt` — risposta
  200 con red flag reale, spiegazione chiaramente etichettata come demo,
  PDF report vero allegato.
