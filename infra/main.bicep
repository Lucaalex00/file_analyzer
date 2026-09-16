@description('Name prefix for all resources')
param namePrefix string = 'filean'

@description('Azure region')
param location string = resourceGroup().location

@description('Public image to deploy (already published by CI, no registry credentials needed)')
param containerImage string = 'ghcr.io/lucaalex00/file_analyzer:latest'

@description('Azure OpenAI endpoint URL. Leave empty to run in demo mode (simulated AI explanations, everything else real) -- see src/api/config.py.')
param azureOpenAiEndpoint string = ''

@secure()
@description('Azure OpenAI API key. Leave empty to run in demo mode.')
param azureOpenAiApiKey string = ''

@description('Azure OpenAI deployment name -- must exist on the resource above (check "Model deployments" in Azure AI Foundry; the available catalog changes over time)')
param azureOpenAiDeployment string = 'gpt-5-mini'

@description('Azure OpenAI API version')
param azureOpenAiApiVersion string = '2024-08-01-preview'

@secure()
@description('Groq API key (free, no approval wait, OpenAI-compatible -- see console.groq.com). Used only if Azure OpenAI is left empty. Leave empty to run in demo mode.')
param groqApiKey string = ''

@description('Groq model name')
param groqModel string = 'openai/gpt-oss-20b'

@description('Total paid AI calls allowed per rolling hour across all visitors -- caps what a public demo link can cost. Past it the app serves simulated explanations instead of failing. 0 disables the cap.')
param aiHourlyBudget int = 60

var logAnalyticsName = '${namePrefix}-logs'
var containerAppEnvName = '${namePrefix}-env'
var containerAppName = '${namePrefix}-app'

// Container Apps rejects a secret with an empty value outright, so only
// declare (and reference) the ones that actually have one -- leaving both
// empty means no secrets and no AI-key env vars at all, same as demo mode
// locally.
var azureSecret = empty(azureOpenAiApiKey) ? [] : [{ name: 'azure-openai-api-key', value: azureOpenAiApiKey }]
var groqSecret = empty(groqApiKey) ? [] : [{ name: 'groq-api-key', value: groqApiKey }]
var azureEnv = empty(azureOpenAiApiKey) ? [] : [{ name: 'AZURE_OPENAI_API_KEY', secretRef: 'azure-openai-api-key' }]
var groqEnv = empty(groqApiKey) ? [] : [{ name: 'GROQ_API_KEY', secretRef: 'groq-api-key' }]

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
      }
      // API keys go through Container Apps' own secret store, referenced
      // by name (secretRef) in the container env below -- never inlined as
      // a plain env var value, so they don't show up in `az containerapp
      // show`/the portal's "Environment variables" view, only in "Secrets"
      // (access-controlled separately).
      secrets: concat(azureSecret, groqSecret)
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: concat([
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
            { name: 'AZURE_OPENAI_API_VERSION', value: azureOpenAiApiVersion }
            { name: 'GROQ_MODEL', value: groqModel }
            { name: 'AI_HOURLY_BUDGET', value: string(aiHourlyBudget) }
          ], azureEnv, groqEnv)
        }
      ]
      // Scales to zero when idle -- no traffic, no cost. The first request
      // after a scale-to-zero period pays a cold-start latency hit; fine for
      // a demo, not something you'd accept for a real production SLA.
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
