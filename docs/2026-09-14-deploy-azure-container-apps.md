# 2026-09-14 — Deploy reale su Azure Container Apps

## Context

La richiesta di aumento quota Azure OpenAI, inviata giorni fa, non ha
ricevuto risposta. Decisione dell'utente: l'obiettivo del progetto è
imparare **Azure**, non specificamente Azure OpenAI — quindi si procede
con tutto ciò che l'ecosistema Azure può insegnare (deploy reale,
infrastruttura, IaC), tenendo Azure OpenAI come pezzo separato, non
bloccante, con GitHub Models come eventuale ripiego futuro.

Il Bicep esistente (`infra/main.bicep`) non aveva mai funzionato davvero:
puntava a un piano Consumption di Azure Functions, che non offre modo di
installare le librerie di sistema (Pango, Cairo, GDK-Pixbuf) richieste da
WeasyPrint — `/health` avrebbe funzionato, `/analyze` no (vedi
[ADR 0001](adr/0001-pdf-generation-weasyprint.md)). Scelto insieme
all'utente: **Azure Container Apps** invece di Functions — usa il
`Dockerfile` del progetto così com'è (nessun adattamento), ha una quota
gratuita reale con scala a zero quando inattivo, e resta comunque
esperienza Azure concreta anche se non è il servizio specifico coperto
dall'AZ-204.

## What changed

- `infra/main.bicep`: riscritto da zero per Container Apps — Log
  Analytics Workspace → Container Apps managed environment (log dirottati
  lì) → Container App (immagine pubblica già pubblicata da CI su GHCR,
  nessun registro privato da configurare). `azureOpenAiEndpoint`/
  `azureOpenAiApiKey` ora opzionali (default vuoto) — il deploy funziona
  anche senza, cadendo in modalità demo esattamente come in locale.
- `infra/README.md`: riscritto con il flusso di deploy corretto e la
  spiegazione del perché Functions non funzionava.
- `README.md`, `OVERVIEW.md`: aggiunta sezione "Live demo" con l'URL
  pubblico reale, sezione Deployment/Roadmap aggiornate.
- Installata Azure CLI (via MSI ufficiale, `winget` non presente nel
  PATH di questa sessione) e autenticato (`az login`).

## Known gap

- La region `westeurope` ha rifiutato la distribuzione ("not accepting
  new customers" — restrizione di capacità legata a questo specifico
  account/sottoscrizione) — usata `swedencentral` invece, stessa region
  già funzionante per la risorsa Azure OpenAI creata in precedenza.
- Nessun Key Vault per i segreti — se in futuro si collegano credenziali
  Azure OpenAI reali al deploy, oggi passerebbero come parametro Bicep
  `@secure()` (mai loggato, ma non centralizzato in un vault) — accettabile
  per un progetto demo, non per produzione.
- Nessuna instrumentazione Application Insights lato codice (solo log
  container raccolti da Log Analytics) — i log strutturati già costruiti
  in `src/observability/ai_tracing.py` arrivano comunque su Log Analytics
  tramite lo stdout del container, senza bisogno di modifiche al codice.

## Verification

- `az bicep build` — sintassi valida.
- `az deployment group validate` — validazione passata su `swedencentral`.
- `az deployment group create` — deploy reale completato
  (`provisioningState: Succeeded`).
- Test end-to-end reale (non mockato) contro l'URL pubblico:
  `/health` → `{"status":"ok","demo_mode":true}`; `/analyze/review` con
  `examples/sample_lease_contract.txt` → red flag reale, spiegazione
  etichettata come demo, come in locale.
- Verifica visiva via Playwright: pagina carica correttamente, banner
  modalità demo visibile, nessun errore in console (solo un 404 innocuo
  su `favicon.ico`, nessuna icona configurata).
