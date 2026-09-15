# UX: barra di progresso stimata durante l'attesa

**Contesto:** dopo i due fix di latenza (
[reasoning_effort](2026-09-15-fix-latenza-analisi.md),
[doppia estrazione](2026-09-15-fix-doppia-estrazione.md)), il tempo totale
per un'analisi con OCR è sceso da ~59s a ~30s (18s estrazione + 12s
chiamata AI), confermato dal pannello di rete del browser dell'utente. È
vicino al minimo fisico per un documento che richiede OCR, dato che
l'estrazione deve necessariamente completarsi prima che l'AI possa
partire.

L'utente ha chiesto di spostare l'attenzione dalla velocità pura alla
percezione dell'attesa: "se riusciamo a giocarcela bene, possiamo
effettivamente tenere occupato chi aspetta" -- in particolare per un
recruiter con poco tempo, 30s di attesa senza segnali di progresso reale
sembrano molto peggio di 30s con un indicatore che si riempie.

## Fix

- `frontend/index.html`: aggiunta una barra di progresso
  (`#status-progress-track` / `#status-progress-fill`) sotto lo spinner e
  il testo rotante già esistenti nel pannello di stato.
- `frontend/styles.css`: stile della barra (traccia sottile, riempimento
  con `transition: width` per un movimento fluido).
- `frontend/app.js`: la barra avanza linearmente verso un tetto del 92%
  in base a una stima di durata totale (30000ms, presa dalle misurazioni
  reali documentate sopra), aggiornata ogni 200ms. Non raggiunge mai il
  100% da sola -- solo la risposta effettiva la fa scattare al 100% (e
  subito dopo il pannello di stato si nasconde) -- così una richiesta più
  lenta del solito non la lascia "bloccata al 100% ma non finita".

Nota: la stima è unica per l'intero ciclo (estrazione residua + analisi),
non due fasi separate -- gestisce correttamente sia il caso comune
(l'anteprima ha già finito l'estrazione quando l'utente clicca "Analizza")
sia il caso di chi clicca subito dopo aver scelto il file.

## Verifica

Nuovo test e2e Playwright: "shows a progress bar that fills up while
analysis is in progress" -- verifica che la barra sia visibile e che la
sua larghezza aumenti nel tempo durante una risposta ritardata. Suite e2e
completa (20 test) verde.
