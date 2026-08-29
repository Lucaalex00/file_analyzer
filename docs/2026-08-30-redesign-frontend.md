# 2026-08-30 — Redesign frontend (temi, accordion, i18n, copia)

## Context

Feedback diretto dell'utente dopo un test manuale: interfaccia troppo
minimale/poco leggibile, nessuna vista testuale dell'analisi (solo il PDF),
nessun modo di copiare il contenuto, nessuna traduzione dell'interfaccia
stessa (solo della spiegazione AI).

## What changed

- `frontend/i18n.js` (nuovo): dizionario per le 5 lingue già supportate
  dall'analisi (it/en/fr/de/es) — etichette statiche dell'interfaccia
  (pulsanti, intestazioni, sottotitolo, dropzone) **e** messaggi d'errore
  (prima solo in italiano, hardcoded in `app.js`). `translate(lang, key)`
  con fallback su italiano poi sulla chiave stessa; `applyTranslations(lang,
  root)` applica le traduzioni a tutti gli elementi `[data-i18n]`.
- `frontend/index.html`: ristrutturato in **accordion** (`<details>`
  nativi, nessun JS per aprire/chiudere) — Testo estratto, **Analisi**
  (nuova sezione: contesto rilevato, riassunto, spiegazione, red flag come
  testo leggibile — prima questi dati arrivavano dall'API ma non venivano
  mai mostrati come testo, solo usati per l'evidenziazione), Report,
  Cronologia. Pulsante "Copia" su Testo estratto e Analisi. Pulsante toggle
  tema in header.
- `frontend/app.js`: `renderAnalysis()` popola la nuova sezione Analisi;
  `copyToClipboard()` (Clipboard API) per i due pulsanti copia;
  `initTheme()`/`applyTheme()` (persistito in `localStorage`, default da
  `prefers-color-scheme` se non impostato); `applyLanguageToUI()` richiamata
  al cambio lingua e al caricamento pagina; messaggi d'errore ora tradotti
  via `i18n.js` invece di un dizionario hardcoded solo italiano.
- `frontend/styles.css`: riscritto — palette coffee/chocolate/beige su
  variabili CSS (`--bg`, `--surface`, `--fg`, `--accent`, ecc.), tema chiaro
  di default e scuro via `[data-theme="dark"]` o `prefers-color-scheme`;
  stile coerente per pulsanti/select con hover e transizioni; stile
  accordion (freccia che ruota, bordo, ombra leggera).
- `e2e/unit/i18n.test.js` (nuovo): 4 test sul modulo i18n.
- `e2e/tests/redesign.spec.js` (nuovo): 5 test E2E — pannello Analisi
  popolato, copia negli appunti (testo estratto e analisi), toggle tema
  persistito dopo reload, cambio lingua traduce le etichette statiche,
  le sezioni sono accordion apribili/chiudibili.

## Known gap

Nessun logo/branding visivo oltre a nome+colore (già gap noto della
feature "branding PDF"). Il layout "prima/dopo" a due colonne è stato
sostituito dall'accordion verticale — trade-off esplicito richiesto
("sezioni minimali"), non più affiancate ma impilate.

## Verification

- `node --test unit/**/*.test.js` (via `make test-frontend-unit`): 12/12
  (4 nuovi per i18n).
- `npx playwright test` (via `make test-e2e`): 14/14 (5 nuovi per il
  redesign), nessuna regressione sui test esistenti nonostante la
  ristrutturazione completa dell'HTML.
- `pytest --cov=src --cov-fail-under=80 -q` + `ruff check src tests`:
  128/128, 96.89% coverage — nessuna modifica al backend in questo giro,
  verificato comunque per sicurezza.
