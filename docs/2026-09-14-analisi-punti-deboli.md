# 2026-09-14 — Analisi punti deboli, semplificazione per recruiter

## Context

Richiesta esplicita dell'utente: un'analisi completa del repository per
trovare punti deboli ed eventualmente renderlo più modulare/semplice da
leggere per un recruiter. Fatto un giro sistematico: struttura del repo,
dimensione dei file sorgente, dipendenze, storia git (nessun segreto mai
committato), coerenza tra documentazione e codice.

## What changed

1. **`src/api/main.py`** — il file sorgente più grande (278 righe) aveva
   lo stesso identico blocco `try/except UnsupportedFileTypeError→415 /
   ExtractionError→422 / AnalysisError→502` ripetuto in 6 endpoint diversi.
   Sostituito con gestori d'eccezione FastAPI globali
   (`@app.exception_handler`) registrati una sola volta da una tabella
   `_ERROR_STATUS_CODES` — gli endpoint ora si limitano a chiamare la
   pipeline e lasciano propagare l'eccezione. L'unica eccezione è
   `/analyze/batch`, che deve continuare a processare gli altri file anche
   se uno fallisce: lì resta un try/except locale, ma riusa la stessa
   funzione di mappatura (`_status_code_for`) invece di duplicare i codici
   di stato. Righe eseguite scese da 152 a 127 (misurate da `--cov`).

2. **`OVERVIEW.md`** era rimasto fermo alla pipeline originale (MVP) e non
   menzionava affatto il lavoro più recente: modalità demo, tracing delle
   chiamate AI, difese prompt injection, ricostruzione a griglia delle
   tabelle OCR, eval regression suite. Aggiunte tre nuove sezioni
   ("Demo mode", "PDF table reconstruction", "AI reliability") e
   aggiornata "Deployment" per riflettere lo stato attuale.

3. **`docs/README.md`** (nuovo) — indice dei 30+ file datati in `docs/`,
   raggruppati per fase (MVP, feature Fase 2, il percorso a tappe del fix
   qualità PDF/OCR, AI reliability e demo mode). Nessun file spostato o
   rinominato — solo un punto d'ingresso per navigare la storia senza
   scorrere una lista piatta di 30 nomi di file.

## Known gap

- Non trovati problemi di sicurezza reali (nessun segreto in git,
  dipendenze pinnate, filename sanitizzati) — l'analisi si è concentrata
  su leggibilità/manutenibilità, non su un audit di sicurezza formale.
- `frontend/app.js` (382 righe, gestisce upload, preview, tema, lingua,
  cronologia, banner demo, copia) potrebbe beneficiare di uno split, ma
  dato il vincolo "niente build step" del progetto, più file `<script>`
  aggiungerebbe overhead di caricamento senza un guadagno chiaro di
  chiarezza — non toccato in questo giro.

## Verification

- Backend: 171/171 test passati (nessun test modificato: il refactor di
  `main.py` cambia solo l'implementazione, non il comportamento HTTP
  osservabile — tutti i test esistenti verificano solo status code, mai
  il contenuto esatto del corpo dell'errore), 97.28% coverage, `ruff
  check` pulito.
- Playwright e2e: 18/18 test passati contro lo stack ricostruito.
