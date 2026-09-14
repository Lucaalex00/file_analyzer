# Infra (demo deploy)

Deploys the app to **Azure Container Apps** for a live demo. Not part of CI —
run manually, record the demo, then tear down to keep costs at zero.

## Why Container Apps, not Azure Functions

An earlier version of this template targeted a plain Consumption-plan Azure
Function. It never actually worked: PDF rendering uses WeasyPrint, which
needs system libraries (Pango, Cairo, GDK-Pixbuf) that a Consumption plan
gives no way to install — `/health` would come up, `/analyze` would fail at
import or render time (see
[`docs/adr/0001-pdf-generation-weasyprint.md`](../docs/adr/0001-pdf-generation-weasyprint.md)).
Container Apps runs the project's own `Dockerfile` as-is (WeasyPrint's
system libraries included) with no adaptation needed, has a real
always-free monthly grant, and scales to zero when idle — no traffic, no
cost.

## No Azure OpenAI credentials required

Leave `azureOpenAiEndpoint`/`azureOpenAiApiKey` empty (the default) and the
deployed app runs in **demo mode** — real extraction, real rule-based red
flags, real PDF generation, simulated AI explanation, clearly labeled as
such (see `src/analyzer/demo_client.py`). Pass real credentials only if you
have a working Azure OpenAI deployment.

## Deploy

```bash
az group create --name file-analyzer-demo --location westeurope

az deployment group create \
  --resource-group file-analyzer-demo \
  --template-file infra/main.bicep

# ... open the containerAppUrl output, record the demo ...

az group delete --name file-analyzer-demo --yes --no-wait
```

To deploy with real Azure OpenAI credentials instead of demo mode, add:

```bash
  --parameters azureOpenAiEndpoint=<your-endpoint> azureOpenAiApiKey=<your-key>
```

The image deployed (`ghcr.io/lucaalex00/file_analyzer:latest`) is the same
one published by CI on every push to `master` — no registry credentials
needed, no local build, no Azure Container Registry to provision.
