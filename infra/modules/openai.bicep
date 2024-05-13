var uniqueId = uniqueString(resourceGroup().id)
var randomSuffix = substring(uniqueId, 0, 4)

@description('Specifies the name of the deployment.')
param name string
@description('Specifies the name of the environment.')
param environment string
@description('Location for all resources.')
param location string 
@description('Specifies the principal ID of the workspace cluster.')
param workspaceClusterPrincipalId string

var openAIServiceName = '${name}-${environment}-openai-${randomSuffix}'


@allowed([
  'S0'
])
param sku string = 'S0'

@description('Creates Azure OpenAI service')
resource resourceOpenAIService 'Microsoft.CognitiveServices/accounts@2021-10-01' = {
  name: openAIServiceName
  location: location
  sku: {
    name: sku
  }
  kind: 'OpenAI'
  properties: {
    customSubDomainName: toLower(openAIServiceName)
    apiProperties: {
      statisticsEnabled: false
    }
  }
}

@description('Deploys mentioned open ai model')
resource openaiModeilDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  name: 'gpt-35-turbo'
  sku: {
    capacity: 10
    name: 'Standard'
  }
  parent: resourceOpenAIService
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-35-turbo'
      version: '0301'
    }
    raiPolicyName: 'Microsoft.Default'
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

@description('Role Assignment to AML cluster to access openai resource')
resource amlContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'openai-contributor')
  scope: resourceOpenAIService
  properties: {
    principalId: workspaceClusterPrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
  }
}

