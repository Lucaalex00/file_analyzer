# 2026-09-15 — Guardrail anti-genericità nel prompt, UX di attesa migliorata

## Context

Prima volta che l'utente testava l'IA reale su più documenti reali. Due
segnalazioni: le spiegazioni erano accurate ma generiche/superficiali
(non ancorate ai dettagli concreti del documento), e la UX di attesa era
solo un testo statico "Analisi in corso...".

## What changed

### Guardrail anti-genericità nel system prompt

`src/analyzer/prompts.py`: `SYSTEM_PROMPT` istruito esplicitamente a
radicare ogni frase di `plain_explanation`/`summary` in dettagli
effettivamente presenti nel documento (nomi, date, importi, durate,
obblighi) invece di frasi generiche applicabili a qualunque documento
dello stesso tipo. Include anche l'istruzione esplicita: se un dettaglio
non è presente, dirlo chiaramente invece di scrivere frasi vaghe per
aggirare l'assenza.

Verificato dal vivo (non con un test automatico, che non può misurare la
qualità di un output LLM reale): la spiegazione ora cita nomi, date,
importi esatti dal documento, e segnala esplicitamente un'informazione
mancante ("il documento non indica l'importo del deposito cauzionale")
invece di scriverci sopra genericamente.

### UX di attesa: spinner + messaggi rotanti

`frontend/index.html`/`app.js`/`styles.css`/`i18n.js`: il messaggio
statico "Analisi in corso..." è sostituito da uno spinner animato + tre
messaggi che ruotano ogni 2,2 secondi ("Stiamo leggendo il documento...",
"Stiamo individuando i punti di attenzione...", "Stiamo scrivendo la
spiegazione..."), tradotti in tutte e 5 le lingue. Sono illustrativi, non
un vero progresso in tempo reale — il backend resta una singola chiamata
request/response, non ha modo di segnalare stadi intermedi al browser;
il commento nel codice lo dichiara esplicitamente per chi legge dopo.

Bug trovato durante la verifica: la regola CSS `#status { display: flex }`
aveva priorità sull'attributo `hidden` del browser (stessa classe di bug
incontrata altre volte in questa sessione con `data-i18n` e overlay CSS) —
serve sempre una regola esplicita `#status[hidden] { display: none; }`
quando si imposta `display` direttamente su un elemento che viene anche
nascosto via attributo `hidden`.

## Known gap

- Nessun test automatico può verificare che le spiegazioni dell'IA siano
  davvero meno generiche — è un miglioramento di prompt engineering,
  verificabile solo manualmente o con revisione umana continua nel tempo.
  Aggiunto solo un test di regressione sul contenuto del prompt stesso
  (garantisce che l'istruzione non sparisca per errore, non garantisce
  che il modello la segua sempre).
- I messaggi di stato rotanti sono generici/illustrativi, non riflettono
  il reale stadio di elaborazione lato server (impossibile con
  un'architettura a singola chiamata request/response).

## Verification

- Backend: 183/183 test passati (2 nuovi: guardrail anti-genericità
  presenti nel prompt), coverage 97.36%, `ruff check` pulito.
- Playwright e2e: 19/19 test passati (nuovo test su spinner + rotazione
  messaggi con risposta mockata rallentata).
- Verifica manuale dal vivo con Azure OpenAI reale: spinner e messaggi
  rotanti visibili durante l'attesa; spiegazione finale con dettagli
  concreti del documento, non generica.
