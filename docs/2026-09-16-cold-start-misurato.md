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
| Avvio della sola app, immagine già locale | **~10,7s** |

Quindi circa **11 dei 19 secondi sono avvio Python nostro**, non
orchestrazione di Azure: import pesanti (WeasyPrint e le sue dipendenze
font, pdfplumber/pdfminer, openai, pytesseract) pagati tutti al caricamento
del modulo, prima che uvicorn possa rispondere a qualsiasi cosa.

## Cosa è stato fatto

Alleggerimento delle dipendenze — `azure-functions` (morto: residuo del piano
originale su Azure Functions, mai importato), l'extra `[standard]` di uvicorn
(uvloop, httptools, websockets, watchfiles, PyYAML: prestazioni inutili per
un servizio che passa ~12s ad aspettare un LLM), `libffi-dev` (header di
compilazione, non runtime).

Risultato onesto: **da 577MB a 561MB**, cioè il 2,8%. La dimensione
dell'immagine non è la leva.

## Cosa resta sul tavolo

1. **Import pigri** per i moduli pesanti (WeasyPrint sopra tutti), così
   uvicorn risponde subito e il costo si paga alla prima generazione di PDF.
   È la leva vera sugli ~11s, ed è gratis.
2. **`minReplicas: 1`** se si vuole azzerare il cold start accettandone il
   costo; con una replica sempre accesa il tetto orario delle chiamate AI
   smette anche di azzerarsi a ogni riavvio, diventando un tetto vero invece
   che un freno.
3. **Fasce orarie** via job schedulato, come compromesso.
