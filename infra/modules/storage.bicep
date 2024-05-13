@description('Specifies the location of the Azure Machine Learning workspace and dependent resources.')
param location string
@description('Specifies the name of the ADLS Gen2 container 1')
param container1Name string
@description('Specifies the name of the ADLS Gen2 container 2')
param container2Name string
@description('The username for the SQL Server admin')
param dbLoginUserName string
@secure()
@description('The password for the SQL Server admin')
param dbLoginPassword string
@description('The name of the SQL Server')
param dbServerName string
@description('The name of the Database')
param databaseName string
@description('The service principal id')
param servicePrincipalId string
@description('The storage account name')
param blobStorageName string

@description('Creates Azure SQL Server')
resource resourceDBServer 'Microsoft.Sql/servers@2019-06-01-preview' = {
  name: dbServerName
  location: location
  properties: {
    administratorLogin: dbLoginUserName
    administratorLoginPassword: dbLoginPassword
    version: '12.0'
    
  }
}

@description('Set Firewall rule to allow azure traffic')
resource sqlFirewallRule 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  name:  'azureAccessFirewall'
  parent: resourceDBServer
  properties: {
    endIpAddress: '0.0.0.0'
    startIpAddress: '0.0.0.0'
  }
}

@description('Creates sql database in server.')
resource resourceDatabase 'Microsoft.Sql/servers/databases@2019-06-01-preview' = {
  parent: resourceDBServer
  name: databaseName
  location: location
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 1073741824 // 1 GB
  }
}

@description('Creates ADLS Gen2 storage account for the gold zone and evaluation data')
resource resourceStorageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: blobStorageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    isHnsEnabled: true
  }
}

@description('Creates blob service to attach to storage account ')
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2021-04-01' = {
  name: 'default'
  parent: resourceStorageAccount
}

@description('Creates ADLS Gen2 Container 1')
resource containerOneADLSGen2 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-04-01' = {
  name:  container1Name
  parent: blobService
}

@description('Creates ADLS Gen2 Container 2')
resource containerTwoADLSGen2 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-04-01' = {
  name: container2Name
  parent: blobService
}

//Role Assignments
@description('Role Assignment to SP for accessing ADLSGen2 containers')
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, 'contributor')
  scope: resourceStorageAccount
  properties: {
    principalId: servicePrincipalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}

@description('Outputs server URI to add to keyvault')
output serverUrl string = resourceDBServer.properties.fullyQualifiedDomainName
