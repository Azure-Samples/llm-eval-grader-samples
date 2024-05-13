var uniqueId = uniqueString(resourceGroup().id)
var randomSuffix = substring(uniqueId, 0, 4)

@description('Specifies the name of the resource group.')
param resourceGroupName string
@description('Specifies the name of the deployment.')
param name string
@description('Specifies the name of the infra deployment environment.')
param environment string
@description('Specifies the location of the Azure Machine Learning workspace and dependent resources.')
param location string
@description('The VM size for compute instance')
param vmSize string = 'Standard_DS3_v2'
@description('The username for the SQL Server admin')
param dbLoginUserName string
@secure()
@description('The password for the SQL Server admin')
param dbLoginPassword string
@description('The SQL Server endpoint')
param serverUrl string
@description('The name of the Database')
param databaseName string
@description('Specifies the name of the ADLS Gen2 container 1')
param container1Name string
@description('Specifies the name of the ADLS Gen2 container 1')
param container2Name string
@secure()
@description('Specifies the client secret for Service Principal')
param clientSecret string
@description('Specifies the client ID for Service Principal')
param clientId string
@description('Specifies the authority URL for the ADLS Gen2 data store')
param authorityUrl string
@description('Specifies the resource URL for the ADLS Gen2 data store')
param resourceUrl string
@description('Specifies the name of the compute cluster')
param clusterName string = 'llm-inspect-cluster'
@description('Specifies the user principal id')
param userPrincipalId string
@description('Specifies the name of the storage account for ADLS Gen2')
param blobStorageName string

var storageAccountName = 'amlst${name}${environment}${randomSuffix}'
var keyVaultName = 'kv-${name}-${environment}-${randomSuffix}'
var applicationInsightsName = 'appl-${name}-${environment}-${randomSuffix}'
var containerRegistryName = 'reg${name}${environment}${randomSuffix}'
var amlWorkspaceName = 'aml${name}${environment}${randomSuffix}'
var logAnalyticsWorkspaceName = 'log-analytics-${name}-${environment}-${randomSuffix}'
var tenantId = subscription().tenantId
var storageAccount = resourceStorageAccount.id
var keyVault = resourceKeyVault.id
var applicationInsights = resourceApplicationInsights.id
var containerRegistry = resourceContainerRegistry.id 

@description('Creates AML Blob Storage Account')
resource resourceStorageAccount 'Microsoft.Storage/storageAccounts@2021-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_RAGRS'
  }
  kind: 'StorageV2'
  properties: {
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
    supportsHttpsTrafficOnly: true
  }
}

@description('Creates Container Registry Resorce for AML')
resource resourceContainerRegistry 'Microsoft.ContainerRegistry/registries@2019-12-01-preview' = {
  sku: {
    name: 'Standard'
  }
  name: containerRegistryName
  location: location
  properties: {
    adminUserEnabled: true
  }
}

@description('Creates log analytics workspace for AML Monitoring and chatbot logs')
resource resourceLogAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

@description('Creates Applocation Insights for AML')
resource resourceApplicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: (((location == 'eastus2') || (location == 'westcentralus')) ? 'southcentralus' : location)
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: resourceLogAnalyticsWorkspace.id
  }
}

@description('Creates Key Vault instance for storing AML as well as application secrets.')
resource resourceKeyVault 'Microsoft.KeyVault/vaults@2021-04-01-preview' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: tenantId
    sku: {
      name: 'standard'
      family: 'A'
    }
    accessPolicies: [
      {
        objectId: userPrincipalId
        tenantId: subscription().tenantId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
          keys: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

@description('Creates AML workspace with all above resources created.')
resource resourceWorkspace 'Microsoft.MachineLearningServices/workspaces@2021-07-01' = {
  identity: {
    type: 'SystemAssigned'
  }
  name: amlWorkspaceName
  location: location
  properties: {
    friendlyName: amlWorkspaceName
    storageAccount: storageAccount
    keyVault: keyVault
    applicationInsights: applicationInsights
    containerRegistry: containerRegistry
  }
  tags: {
    createdBy: 'Bicep Script'
  }
}

@description('Creates AML Compute Cluster')
resource workspaceCluster 'Microsoft.MachineLearningServices/workspaces/computes@2021-07-01' = {
  parent: resourceWorkspace
  name: clusterName
  location: location
  properties: {
    computeType: 'AmlCompute'
    properties: {
      vmSize: vmSize
      scaleSettings: {
        minNodeCount: 1
        maxNodeCount: 4
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
  tags: {
    createdBy: 'Bicep Script'
  }
} 

@description('Creates datastore in AML for ADLS Gen2 container 1')
resource adlsGen2ContainerOneDatastore 'Microsoft.MachineLearningServices/workspaces/datastores@2023-10-01' = {
  parent: resourceWorkspace
  name: replace(container1Name, '-', '')
  properties: {
    credentials: {
      credentialsType: 'ServicePrincipal'
      authorityUrl: authorityUrl
      clientId: clientId
      resourceUrl: resourceUrl
      secrets: {
        clientSecret: clientSecret
        secretsType: 'ServicePrincipal'
      }
      tenantId: tenantId
    }
    datastoreType: 'AzureDataLakeGen2'
    accountName: blobStorageName
    filesystem: container1Name
    resourceGroup: resourceGroupName
    subscriptionId: subscription().subscriptionId
  }
}

@description('Creates datastore in AML for ADLS Gen2 container 2')
resource adlsGen2ContainerTwoDatastore 'Microsoft.MachineLearningServices/workspaces/datastores@2023-10-01' = {
  parent: resourceWorkspace
  name: replace(container2Name, '-', '')
  properties: {
    credentials: {
      credentialsType: 'ServicePrincipal'
      authorityUrl: authorityUrl
      clientId: clientId
      resourceUrl: resourceUrl
      secrets: {
        clientSecret: clientSecret
        secretsType: 'ServicePrincipal'
      }
      tenantId: tenantId
    }
    datastoreType: 'AzureDataLakeGen2'
    accountName: blobStorageName
    filesystem: container2Name
    resourceGroup: resourceGroupName
    subscriptionId: subscription().subscriptionId
  }
}

// Access Policy and Role Assignments
@description('Keyvault access policy to allow AML cluster to acces KeyVault.')
resource keyVaultAccessPolicy 'Microsoft.KeyVault/vaults/accessPolicies@2021-06-01-preview' = {
  parent: resourceKeyVault
  name: 'add'
  properties: {
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: workspaceCluster.identity.principalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
          keys: [
            'get'
            'list'
          ]
          certificates: []
        }
      }
    ]
  }
}

@description('Role Assignment for AML cluster to access log analytics for reading chatbot logs')
resource analyticsLogsRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'aml-', clusterName, 'analyticsLogsRoleAssignment')
  scope: resourceLogAnalyticsWorkspace
  properties: {
    principalId: workspaceCluster.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '73c42c96-874c-492b-b04d-ab87d138a893')
  }
}

@description('Role Assignment for AML Cluster to perform all operations on AML')
resource amlDataScientisRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'aml-', clusterName, 'contributor')
  scope: resourceWorkspace
  properties: {
    principalId: workspaceCluster.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
  }
}

//Adds Secrets to Keyvault
@description('Adds sql server uri to keyvault')
resource databaseServerNameSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: resourceKeyVault
  name: 'azuresqlserver'
  properties: {
    value: serverUrl
  }
}

@description('Adds database username to keyvault')
resource databaseLoginSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: resourceKeyVault
  name: 'azuresqlserver-user'
  properties: {
    value: dbLoginUserName
  }
}

@description('Adds database password to keyvault')
resource databasePasswordSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: resourceKeyVault
  name: 'azuresqlserver-password'
  properties: {
    value: dbLoginPassword
  }
}

@description('Adds database name to keyvault')
resource databaseSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: resourceKeyVault
  name: 'azuresqlserver-database'
  properties: {
    value: databaseName
  }
}

@description('Adds log analytics workspace id to keyvault')
resource logAnalyticsWorkspaceIdSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: resourceKeyVault
  name: 'sample-chatbot-az-monitor-workspace-id'
  properties: {
    value: resourceLogAnalyticsWorkspace.properties.customerId

  }
}


@description('Output log analytics resource id to attach to application insights resource')
output logAnalyticsResourceId string = resourceId(resourceGroupName, 'Microsoft.OperationalInsights/workspaces', logAnalyticsWorkspaceName)

@description('Output AML Cluster id for providing access to other resources in resource group.')
output workspaceClusterPrincipalId string = workspaceCluster.identity.principalId

