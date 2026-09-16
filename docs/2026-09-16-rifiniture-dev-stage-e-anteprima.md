# 2026-09-16 — Stage dev, anteprima social, viewport

## Context

Tre rifiniture indipendenti emerse mentre si chiudeva il progetto, tenute
insieme solo dal fatto di essere piccole.

La prima è attrito di sviluppo: ogni ricostruzione dell'immagine faceva
sparire `pytest` dal container, perché era stato installato a mano dentro
un'istanza in esecuzione. Le altre due sono difetti visibili a chi riceve il
link.

## What changed

**Stage `dev` nel Dockerfile.** L'immagine di produzione diventa lo stage
`base`, `dev` ci aggiunge sopra il tooling di test, e un terzo stage
`runtime` chiude il file. L'ordine conta: una `docker build` senza
`--target` — quella con cui la CI pubblica — prende l'**ultimo** stage,
quindi la produzione deve stare in fondo. `docker-compose.yml` costruisce
esplicitamente `target: dev`, così dopo un clone basta
`docker compose exec api python -m pytest`. Aggiunti i target `make test`
(nel container) e `make test-local` (sull'host).

**Meta tag Open Graph.** Il link condiviso su LinkedIn o via mail non
mostrava alcuna anteprima. Aggiunti titolo, descrizione e immagine (lo
screenshot dell'analisi servito da GitHub raw), con URL assoluti perché gli
scraper che costruiscono le anteprime non eseguono JavaScript e non
risolvono percorsi relativi.

**Meta viewport, che mancava del tutto.** Senza, il telefono renderizzava la
pagina a larghezza desktop e poi la rimpiccioliva: tutto il lavoro sul layout
responsive c'era, ma non veniva mai applicato su mobile.

## Known gap

L'immagine di anteprima punta a un file nel branch `master` su GitHub: se il
repo diventasse privato, l'anteprima smetterebbe di funzionare senza che
nulla nel sito segnali il problema.

`og:url` contiene l'indirizzo della demo su Azure scritto a mano: se il
Container App venisse ricreato con un altro nome, andrebbe aggiornato lì.

## Verification

- Build di produzione verificata esplicitamente priva di `pytest` e
  `watchfiles`, e con l'app importabile.
- `docker compose exec api python -m pytest` funzionante subito dopo una
  ricostruzione: 212 test verdi, più 28 e2e contro lo stage `dev`.
- Meta tag verificate servite dalla demo pubblica dopo il deploy.
