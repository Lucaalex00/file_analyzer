# Fix: la preview del testo estratto falliva senza dire nulla

## Contesto

L'utente ha caricato un'immagine (un logo) per verificare il fix
precedente (rifiuto di immagini senza testo affidabile) e ha segnalato che
non succedeva nulla: nessun testo estratto, nessun errore, niente. Prima
dei fix recenti la preview mostrava sempre qualcosa (anche se garbled); ora
che l'estrazione può correttamente fallire con un errore chiaro (immagine
senza testo affidabile, PDF illeggibile, ecc.), quel fallimento veniva
silenziato di proposito nella preview automatica al caricamento del file —
per design, il commento nel codice diceva che l'errore "definitivo" sarebbe
comparso solo cliccando Analizza.

Questo design va bene quando l'estrazione funziona silenziosamente in
background, ma quando fallisce dà l'impressione che l'app sia bloccata o
rotta, senza nessun feedback.

## Cosa è cambiato

`frontend/app.js`, `showExtractedTextPreview()`: invece di ignorare
silenziosamente una risposta non-ok o un errore di rete, ora mostra subito
il messaggio di errore tradotto (stesso banner usato per gli errori di
Analizza), così l'utente sa immediatamente che l'estrazione è fallita e
perché, senza dover cliccare Analizza per scoprirlo.

## Verification

- Playwright e2e: 16/16 test passati (nuovo test che verifica che un
  fallimento di `/extract` mostri subito il banner di errore, non il
  pannello del testo estratto).
- Frontend unit: 12/12 test passati.
