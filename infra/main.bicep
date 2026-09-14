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

@description('Azure OpenAI deployment name')
param azureOpenAiDeployment string = 'gpt-4o-mini'

@description('Azure OpenAI API version')
param azureOpenAiApiVersion string = '2024-08-01-preview'

var logAnalyticsName = '${namePrefix}-logs'
var containerAppEnvName = '${namePrefix}-env'
var containerAppName = '${namePrefix}-app'

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
          env: [
            { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAiEndpoint }
            { name: 'AZURE_OPENAI_API_KEY', value: azureOpenAiApiKey }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: azureOpenAiDeployment }
            { name: 'AZURE_OPENAI_API_VERSION', value: azureOpenAiApiVersion }
          ]
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
