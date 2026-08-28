# 2026-08-28 — Frontend minimale: design

## Context

Primo item "frontend" del backlog Fase 2 (`docs/2026-08-28-fase2-roadmap.md`,
priorità 4): oggi il progetto ha solo un'API, nessuna interfaccia visiva. Un
frontend minimale con preview del risultato è il primo contatto per un
recruiter/utente e sblocca le feature successive che dipendono dalla UI
(preview prima/dopo, cronologia locale, explainability).

## Decisioni

- **Stack**: HTML/CSS/JS vanilla, nessuna build step, nessuna dipendenza
  Node/npm.
- **Serving**: stesso servizio FastAPI. `frontend/` alla radice del repo
  (`index.html`, `app.js`, `styles.css`), montata come file statici
  (`/static`), `index.html` servito sulla root `/`. Nessun nuovo container.
- **Visualizzazione risultato**: il PDF ricevuto viene mostrato inline
  (`<embed>` su un Object URL) più un link di download che riusa lo stesso
  blob, col nome file preso dall'header `Content-Disposition`.
- **Testing**: E2E con Playwright contro il backend reale in Docker
  (coerente con l'approccio già usato in TaskFlow).

## Flusso pagina

1. Drag&drop o `<input type="file">`, validazione lato client
   dell'estensione (`.pdf/.txt/.docx`) — solo UX, il backend resta
   l'autorità.
2. Submit → `fetch('/analyze', {method: 'POST', body: formData})`, stato
   "Analisi in corso..." durante l'attesa.
3. Successo → PDF mostrato inline + link download.
4. Errore (413/415/422/502) → messaggio leggibile per status code, mai JSON
   grezzo.

## Known gap

Nessuna preview "prima/dopo" (testo estratto vs spiegazione) in questa
prima versione — è la feature successiva del backlog, costruita sopra
questa base.
