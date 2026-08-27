# Infra (demo deploy)

Deploys the Function App for a live demo. Not part of CI — run manually, record
the demo, then tear down to keep costs at zero.

## Caveat: `/analyze` will not work on a Consumption plan as-is

PDF rendering uses WeasyPrint, which needs system libraries (Pango, Cairo,
GDK-Pixbuf) — see
[`docs/adr/0001-pdf-generation-weasyprint.md`](../docs/adr/0001-pdf-generation-weasyprint.md).
A Consumption plan gives no mechanism to install system packages, so expect
`/health` to work post-deploy while `/analyze` fails at import or render time.
Do not attempt this deploy blind. The two real options identified in the ADR
are: (a) run the app as a **containerized Function on a Flex Consumption or
Premium plan**, reusing the project `Dockerfile` which already installs those
libraries, or (b) swap the renderer for **`xhtml2pdf`**, a pure-Python
HTML-to-PDF renderer with no native dependencies but weaker CSS support. This
Bicep template targets the plain Consumption plan and is kept as a starting
point, not a working end-to-end deploy.

```bash
az group create --name file-analyzer-demo --location westeurope

az deployment group create \
  --resource-group file-analyzer-demo \
  --template-file infra/main.bicep \
  --parameters azureOpenAiApiKey=<your-key> azureOpenAiEndpoint=<your-endpoint>

func azure functionapp publish <functionAppName-from-output>

# ... record the demo ...

az group delete --name file-analyzer-demo --yes --no-wait
```
