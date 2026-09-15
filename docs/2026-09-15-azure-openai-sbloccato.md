# 2026-09-15 — Azure OpenAI sbloccato, fix httpx, integrazione Groq

## Context

Dopo giorni di attesa senza risposta sulla richiesta di aumento quota,
l'utente ha scoperto che il problema reale era un dettaglio della
sottoscrizione (pagamento in base al consumo non impostato correttamente)
— non un problema di quota AI in sé. Sistemato lato Azure dall'utente,
riprovato: il deployment del modello ora funziona.

Nel frattempo (mentre si aspettava una risposta), era già stata costruita
un'integrazione con **Groq** come provider AI alternativo (gratis, nessuna
approvazione, API compatibile OpenAI) — utile comunque come rete di
sicurezza indipendentemente da come sarebbe andata a finire con Azure.

## What changed

### Azure OpenAI: sbloccato, ma con un modello diverso

`gpt-4o-mini` non è più disponibile per nuovi deployment (deprecato dal
catalogo). Usato `gpt-5-mini` al suo posto — verificato via Azure CLI
l'elenco dei modelli disponibili e non deprecati, deployato dall'utente
nel portale Foundry. Aggiornato il default `AZURE_OPENAI_DEPLOYMENT` in
tutto il progetto (`src/api/config.py`, `docker-compose.yml`,
`infra/main.bicep`, `.env.example`) da `gpt-4o-mini` a `gpt-5-mini`.

### Bug reale trovato e sistemato: conflitto `openai`/`httpx`

Primo vero tentativo di chiamata Azure OpenAI di questa sessione,
risultato in `TypeError: Client.__init__() got an unexpected keyword
argument 'proxies'`. Causa: `openai==1.51.0` (pinnata in
`requirements.txt`) passa internamente `proxies` a `httpx`, parametro
rimosso da `httpx>=0.28`. `httpx` non era pinnata, quindi l'ultima build
Docker aveva scaricato una versione troppo recente. Aggiunto `httpx<0.28`
a `requirements.txt` — bug reale, non specifico ad Azure, sarebbe successo
con qualunque client basato su `openai` SDK a questa versione.

### Groq come terzo provider (non solo Azure/demo)

`src/api/dependencies.py`: `_build_ai_client_and_model()` ora sceglie tra
tre provider, in ordine di priorità: Azure OpenAI (se configurato) →
Groq (se configurato) → demo mode. Groq è compatibile con l'API OpenAI
(`base_url="https://api.groq.com/openai/v1"`), quindi basta il client
`openai.OpenAI` standard, nessuna classe nuova necessaria — a differenza
di `DemoAIClient`, che duck-typa la stessa superficie ma non è un vero
client HTTP.

`Settings` guadagna `has_azure_openai`, `has_groq`, `ai_provider`
("azure_openai" | "groq" | "demo") — `/health` ora espone anche
`ai_provider` oltre a `demo_mode`, per sapere sempre con certezza quale
motore sta rispondendo.

## Known gap

- Il deploy pubblico su Azure Container Apps (vedi
  [2026-09-14](2026-09-14-deploy-azure-container-apps.md)) resta
  volutamente in demo mode — nessuna credenziale reale (Azure OpenAI né
  Groq) collegata. Collegarne una esporrebbe la quota reale a chiunque
  trovi l'URL pubblico. Le credenziali reali restano solo nell'`.env`
  locale, non nel deploy pubblico.
- GitHub Models (menzionato come piano B nei giorni scorsi) è stato
  scoperto **completamente ritirato** dal 30 luglio 2026 — informazione
  che le mie ricerche iniziali non avevano colto (basate su fonti non
  aggiornate). Groq lo sostituisce nel ruolo di "provider gratuito senza
  attesa".

## Verification

- Backend: 181/181 test passati (nuovi test su `has_azure_openai`,
  `has_groq`, `ai_provider`, selezione client Groq/Azure/demo in
  `dependencies.py`), 97.36% coverage, `ruff check` pulito.
- Playwright e2e: 18/18 test passati.
- **Primo test end-to-end reale con Azure OpenAI di tutta la sessione**:
  `examples/sample_lease_contract.txt` → spiegazione fluente in italiano,
  osservazioni genuine (non template), non solo i red flag rule-based.
- Bicep validato di nuovo (`az deployment group validate`) dopo l'aggiunta
  dei parametri Groq — ancora `Succeeded`.
