# 2026-09-20 — Un eval contro il modello vero (e cosa ha trovato subito)

## Context

L'audit dello strato di affidabilità aveva lasciato scoperto il pezzo più
importante: **nessun test falliva se una modifica al prompt o al modello
peggiorava la qualità reale**. La suite in `tests/eval/` usa risposte finte,
quindi verifica il cablaggio (schema, merge, rete di sicurezza), non il
modello — e lo dichiara onestamente nel proprio docstring.

Il set di valutazione però esisteva già, sparso in questo diario: ogni voce
che documenta un fallimento osservato è un caso con un comportamento atteso
noto. Spiegazioni generiche, date giudicate male, citazioni inventate,
prompt injection. Guasti trovati sul campo, non immaginati a tavolino.

## What changed

**`tests/eval/test_live_quality.py`**, marcato `live` ed escluso dalla suite
normale via `addopts = -m "not live"`. Si lancia con `make eval`. Non sta in
CI di proposito: richiede credenziali vere, costa chiamate e non è
deterministico, quindi un rosso in CI significherebbe "oggi il modello ha
tirato male" tanto spesso quanto "hai rotto qualcosa".

Misura **proprietà verificabili contro il documento stesso**, mai uguaglianza
con un testo atteso (che un modello stocastico non riprodurrebbe e che non
misurerebbe nulla): ogni citazione esiste davvero nel testo; ogni controllo
deterministico compare al massimo una volta; i controlli attesi sono
scattati; quelli vietati no; la spiegazione nomina gli importi e le date del
documento; il contesto è fra quelli plausibili.

I risultati vanno in `tests/eval/baseline.json`, committata: una proprietà
che reggeva quando è stata registrata e che non regge più è una regressione.
`make eval-update` la riscrive, da leggere prima di committare.

`RedFlag` ha ora `rule_id`: dopo la fusione sopravvive la formulazione del
modello, tradotta, quindi il titolo non dice più quale controllo
deterministico sia scattato. L'id sì, in qualunque lingua — serve all'eval e
renderebbe mostrabile la provenienza anche nel report.

## Cosa ha trovato al primo lancio

**Azure OpenAI rifiuta i documenti che contengono tentativi di prompt
injection** (HTTP 400, `jailbreak: detected`). Il documento non veniva
analizzato affatto, i tre tentativi fallivano e l'utente riceveva un 502
generico — mentre il README dichiarava (riga 181) che un tentativo di
injection è *"a visible red flag, not a hard block — the document is still
analyzed"*. Era falso in produzione.

Due correzioni: gli errori permanenti (4xx diversi da 429) non vengono più
ritentati, perché tre tentativi su un verdetto identico bruciavano solo
budget; e un rifiuto ora degrada ai **soli controlli deterministici**, con
una spiegazione che dichiara apertamente che l'AI ha rifiutato. Su un
documento rifiutato sono proprio quei controlli a contare: ciò che scatena il
rifiuto è l'injection, che le regole rilevano. Chiude anche il limite
"nessun fallback a metà richiesta" già dichiarato fra i limiti noti.

**La regola sul rinnovo automatico aveva un punto cieco.** Il pattern
accettava `renews automatically` ma non `automatically renews`, né il titolo
`Automatic renewal:` — cioè le forme che un contratto vero usa più spesso. La
suite a risposte finte non poteva accorgersene: la sua fixture era scritta
per combaciare col regex.

## Known gap

Due delle sei proprietà iniziali erano mal progettate e sono state corrette
*dopo* aver visto i dati, non prima: cercavano i titoli italiani delle regole
(che dopo la fusione non esistono più) e trattavano come difetto due rilievi
del modello che citano la stessa frase (legittimo: una frase può portare due
rischi). Vale la pena dirlo, perché un eval che si adatta ai risultati è un
eval che non misura niente — qui l'adattamento è stato sulle proprietà
sbagliate, non sulle soglie.

Il corpus è di sei documenti sintetici brevi. Non copre OCR (servirebbero
scansioni reali), né documenti lunghi, né lingue oltre a inglese e italiano.

La baseline registra un singolo campione per caso: su una proprietà al limite
un rosso può essere il modello che ha tirato male. Le proprietà scelte sono
quasi tutte deterministiche proprio per ridurre questo, ma `quote_coverage` è
una percentuale e ha una tolleranza esplicita del 15%.

## Verification

237 test nella suite normale (l'eval live escluso), `ruff` pulito, 28 e2e.

L'eval live: sei casi, tutte le proprietà rispettate, baseline registrata e
riverificata con una seconda esecuzione andata a buon fine. Le due correzioni
al prodotto descritte sopra sono nate da quel primo rosso.
