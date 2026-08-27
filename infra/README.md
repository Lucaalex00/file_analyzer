# Infra (demo deploy)

Deploys the Function App for a live demo. Not part of CI — run manually, record
the demo, then tear down to keep costs at zero.

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
