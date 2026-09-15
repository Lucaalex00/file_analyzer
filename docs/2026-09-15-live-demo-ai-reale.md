# 2026-09-15 — Deploy pubblico aggiornato con Azure OpenAI reale

## Context

Richiesta dell'utente, subito dopo lo sblocco di Azure OpenAI: collegare
le credenziali reali al deploy pubblico su Azure Container Apps (vedi
[2026-09-14](2026-09-14-deploy-azure-container-apps.md)), non solo
all'ambiente locale, per poter testare l'analisi AI vera anche dal link
pubblico.

## What changed

- `infra/main.bicep`: le chiavi API (Azure OpenAI e Groq) passano ora
  attraverso i **secrets nativi di Container Apps** (`secretRef`), non
  più come valore semplice della variabile d'ambiente — non compaiono
  nella vista "Environment variables" del portale/CLI, solo in "Secrets"
  (controllo accessi separato). Gestiti come opzionali: se una chiave è
  vuota, il relativo secret e la relativa variabile d'ambiente vengono
  del tutto omessi dal deployment invece di essere inviati vuoti —
  Container Apps rifiuta esplicitamente un secret con valore vuoto
  (`ContainerAppSecretInvalid`), scoperto al primo tentativo di redeploy.
- Rideployato `file-analyzer-demo` con le credenziali reali della risorsa
  `openai-file-analyzer` (endpoint + chiave recuperati via CLI, mai
  scritti su file, passati solo come parametri di deploy).

## Known gap

- Il deploy pubblico ora espone la quota Azure OpenAI reale a chiunque
  trovi l'URL. Unica protezione: rate limiting a 20 richieste/minuto per
  IP (già esistente, non specifico a questo deploy). Se emergono costi
  anomali o abusi, il rollback è immediato: ridistribuire senza i
  parametri `azureOpenAiEndpoint`/`azureOpenAiApiKey` riporta il deploy in
  demo mode.

## Verification

- `az bicep build` — sintassi valida dopo il fix dei secrets condizionali.
- `az deployment group create` — `provisioningState: Succeeded`.
- Test end-to-end reale contro l'URL pubblico: `/health` →
  `{"status":"ok","demo_mode":false,"ai_provider":"azure_openai"}`;
  `/analyze/review` con `examples/sample_lease_contract.txt` → spiegazione
  reale in italiano, non simulata.
