# Cold start: misurarlo prima di pagarlo

**Contesto:** con `minReplicas: 0` la demo pubblica scala a zero quando è
inattiva, e chi apre il link a freddo aspetta. Subito dopo tre deploy avevo
misurato 90s, 47s e 72s, il che sembrava un problema grave. La proposta
naturale era un job schedulato che tenesse l'app sveglia con dei ping.

## Perché il job di keep-alive non è la risposta

Su Container Apps consumption si paga la replica *mentre gira*. Un ping ogni
pochi minuti tiene una replica accesa 24 ore su 24: è esattamente la spesa di
`minReplicas: 1`, ottenuta però per vie traverse e con più modi di sbagliare
— il cron di GitHub Actions può slittare oltre i 5 minuti di `cooldownPeriod`
(e allora il cold start ritorna), e GitHub disattiva i workflow schedulati
dopo 60 giorni di inattività del repo.

Un job ha senso solo per una cosa che `minReplicas: 1` non sa fare da solo:
**tenere l'app calda a fasce orarie** (alzare `minReplicas` la mattina e
rimetterlo a 0 la sera), che costa circa la metà. Richiede però una
credenziale Azure nei secret del repo.

## Le misure

I 47-72s iniziali erano fuorvianti: li avevo presi **subito dopo un deploy**,
quindi includevano il primo pull di un'immagine nuova su un nodo fresco (e in
un caso una revisione andata in `ActivationFailed`, poi rientrata da sola).

A regime, con i layer già sul nodo:

| | |
|---|---|
| Cold start totale (richiesta a freddo, scale-to-zero) | **~19s** |
| di cui rete (DNS + TCP + TLS) | 0,35s |
| Avvio container completo fino alla prima risposta | ~3,5s |
| di cui overhead di Docker Desktop su Windows (inesistente su Azure) | ~1,5s |
| Import dell'intera applicazione (`src.api.main`) | **1,35s** |
| Somma di tutti gli import pesanti | 1,9s (weasyprint 675ms, openai 623ms, resto trascurabile) |

**Circa 2 dei 19 secondi sono nostri.** Gli altri ~17 sono piattaforma:
allocazione del nodo, pull e mount dell'immagine, avvio del container.

### Una misura sbagliata, e perché

La prima volta avevo misurato 10,7s di avvio dell'app e concluso che oltre
metà del cold start fosse codice nostro. Era un artefatto: quella misura era
la prima esecuzione **subito dopo la build**, con l'immagine ancora fredda e
Docker Desktop che si stava scaldando. Ripetuta a immagine calda: 3,5s.

La conseguenza pratica è opposta a quella che avevo tratto: rendere pigri gli
import di WeasyPrint & co. risparmierebbe frazioni di secondo su diciannove,
e **non vale la modifica**. È il motivo per cui questa pagina esiste — la
prima misura plausibile aveva mandato l'ottimizzazione nella direzione
sbagliata.

## Cosa è stato fatto

Alleggerimento delle dipendenze — `azure-functions` (morto: residuo del piano
originale su Azure Functions, mai importato), l'extra `[standard]` di uvicorn
(uvloop, httptools, websockets, watchfiles, PyYAML: prestazioni inutili per
un servizio che passa ~12s ad aspettare un LLM), `libffi-dev` (header di
compilazione, non runtime).

Risultato onesto: **da 577MB a 561MB**, cioè il 2,8%. La dimensione
dell'immagine non è la leva.

## Cosa resta sul tavolo

Visto che il codice vale ~2 dei 19 secondi, non esiste una leva gratuita che
sposti davvero l'ago. Restano solo scelte che costano:

1. **`minReplicas: 1`**: azzera il cold start, si paga una replica sempre
   accesa. Con una replica viva il tetto orario delle chiamate AI smette
   anche di azzerarsi a ogni riavvio, diventando un tetto vero invece che un
   freno.
2. **Fasce orarie** via job schedulato che alza e abbassa `minReplicas`:
   circa metà costo, zero cold start quando serve.
3. **Non fare nulla** e dirlo: il README già avvisa che la prima richiesta
   sveglia il servizio. Per un progetto dimostrativo è una posizione
   difendibile, e costa zero.
