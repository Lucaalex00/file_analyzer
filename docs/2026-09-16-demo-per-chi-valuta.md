# Rendere la demo leggibile a chi deve valutarla in trenta secondi

**Contesto:** valutazione onesta del progetto dal punto di vista di un
recruiter o di un'azienda. Il punto debole non era il codice ma il *primo
minuto*: chi apre il link pubblico trova una dropzone vuota, deve cercare un
file suo, caricarlo e aspettare ~30s prima di vedere qualsiasi cosa. E tutta
la parte ingegneristica (test, IaC, fallback tra provider, log delle
decisioni) è invisibile a chi non apre GitHub.

## Cosa è stato fatto

**1. Documenti di esempio con un click** (`src/api/example_documents.py`)

Sotto il pulsante Analizza compaiono dei documenti già pronti: un click
carica il file *e avvia l'analisi*, senza passare dal file picker. Quel
primo click è l'unica attenzione che un visitatore dà davvero. Risolve anche
un problema di fiducia: nessuno carica un contratto vero sul sito di uno
sconosciuto.

L'id nell'URL è una chiave in una allowlist, mai un percorso — costruire un
path dalla richiesta avrebbe reso l'endpoint una lettura di file arbitraria.
Le voci il cui file non esiste non vengono offerte, così la lista degrada
invece di dare 404.

**2. Documentazione apribile dal sito** (`src/api/project_docs.py`)

Un pulsante in alto a destra apre un pannello con README, architettura
(OVERVIEW) e limiti noti, renderizzati da Markdown a HTML lato server. I
link relativi vengono riscritti verso GitHub, così continuano a funzionare
dentro il pannello. Stessa allowlist rigida degli esempi.

**3. Lingua iniziale dal browser** (`frontend/app.js`)

Prima la pagina partiva sempre in italiano. Ora usa la lingua del browser se
è tra quelle supportate, altrimenti ripiega sull'inglese (non sull'italiano):
il pubblico di questa demo è anche internazionale.

**4. Tetto orario alle chiamate AI** (`src/api/ai_budget.py`)

Il rate limit per IP protegge da un singolo visitatore, non dal conto totale
di un link pubblico collegato a un modello a pagamento. `AIBudget` conta le
chiamate in una finestra scorrevole di un'ora (default 60, configurabile via
`AI_HOURLY_BUDGET`, anche nel Bicep). Superato il tetto `BudgetedAIClient`
passa al client demo invece di fallire: chi apre il link trova sempre un
sito funzionante, con le spiegazioni simulate ed etichettate come tali —
`/health` riporta `demo_mode: true`, quindi il banner esistente compare da
solo.

**5. Favicon** — mancava del tutto (404 in console).

## Bug reali trovati strada facendo

- **`README.md`, `OVERVIEW.md` ed `examples/` non erano nell'immagine
  Docker** (esclusi da `.dockerignore`, non copiati dal Dockerfile). Le due
  funzionalità nuove leggono quei file a runtime: in locale funzionavano per
  via dei volumi, in produzione sarebbero fallite. Aggiunti al Dockerfile e
  sbloccati nel `.dockerignore`.
- **Il conteggio dei test riportato durante la sessione era gonfiato.** Un
  `docker cp` sbagliato aveva lasciato una copia duplicata di `tests/` dentro
  il container e pytest la contava due volte. Il numero reale è 210, non i
  ~370 riportati prima. Ora `tests/` è montato come volume, così il duplicato
  non si può più formare.

## Verifica

- Backend: 210 test (nuovi: budget orario, client con budget, endpoint docs
  ed esempi, incluso che i tentativi di path traversal non risolvano file).
- e2e: 27 test (nuovi: un click su un esempio esegue tutta l'analisi, il
  pannello docs apre il README e l'architettura, la lingua iniziale segue il
  browser e ripiega sull'inglese).
- Unit frontend: 12.
