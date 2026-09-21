# 2026-09-21 — Il costo dell'analisi, mostrato in pagina

## Context

I token consumati da ogni analisi erano stati aggiunti ai log il giorno
prima, ma l'utente li cercava nell'interfaccia e non li trovava: finivano
solo nei log del server, visibili dal portale Azure. Osservabilità che, per
chi non apre né un terminale né i log, semplicemente non esiste.

La ragione per mostrarli non è l'utente finale — a chi carica un contratto
non interessa quanti token sono serviti. È che questo progetto viene guardato
anche da chi valuta come è costruito, e il lavoro sul controllo dei costi
(tetto orario, degrado, budget) è tutto sepolto nel codice: nessuno legge
`ai_budget.py`, ma un numero accanto al risultato lo vede.

## What changed

`/analyze/review` restituisce ora un oggetto `metrics` con i token totali e
la durata. Il conteggio arriva dal provider e attraversa il pipeline tramite
un dizionario **passato dal chiamante**: `analyze(..., metrics=...)` lo
riempie se c'è. L'alternativa ovvia — tenere l'ultimo uso sull'analizzatore —
sarebbe stata una race condition, perché l'analizzatore è un singleton in
cache condiviso fra richieste concorrenti. Le firme esistenti restano
compatibili: il parametro è opzionale e nessun chiamante attuale è stato
toccato.

La durata è misurata **nell'endpoint**, non nell'analizzatore: ciò che conta
è quanto ha aspettato l'utente, estrazione e generazione del PDF incluse, non
la sola chiamata al modello.

In pagina è una riga discreta accanto ai pulsanti di download, in carattere
piccolo e colore attenuato: `2.363 token · 13,1 s`.

Il primo tentativo l'aveva messa in fondo al pannello dell'analisi, ed era
sbagliato: quel pannello ha un proprio scorrimento, quindi sotto contesto,
riassunto, spiegazione e cinque punti di attenzione la riga finiva centinaia
di pixel oltre la sua piega — presente nel DOM e invisibile a chiunque. Il
test e2e non se n'è accorto perché verificava `toBeVisible()`, che per
Playwright significa soltanto "esiste e ha dimensioni". Ora verifica che
l'elemento **non sia dentro** il pannello che scorre, che è la proprietà che
si intendeva davvero.
Quando il provider non riporta l'uso — modalità demo, o documento rifiutato —
i token spariscono dalla riga e resta solo il tempo: dire "0 token" sarebbe
un numero, e sbagliato. Riaprendo una voce di cronologia la riga non compare
affatto, perché non c'è nessuna esecuzione da descrivere.

## Known gap

Il numero mostrato è dei token, non del costo in euro: convertirlo
richiederebbe il prezzo per modello, che cambia nel tempo e per regione, e un
prezzo sbagliato sarebbe peggio di nessun prezzo.

Il tetto orario continua a contare le chiamate e non i token, anche ora che i
token sono noti ovunque servano.

## Verification

239 test backend, 30 e2e (due nuovi: la riga compare con i valori attesi, e
resta nascosta quando non ci sono metriche), `ruff` pulito.

Provato contro il modello vero: `{'total_tokens': 2363, 'duration_ms': 43909}`.
I 44 secondi hanno anche mostrato il valore del tracing — il log diceva
`attempt 1/3 transient_error 30619ms APITimeoutError` seguito da
`attempt 2/3 success 13129ms`: un timeout del client a 30s e un secondo
tentativo riuscito. Senza traccia sarebbe rimasto un "a volte è lento".
