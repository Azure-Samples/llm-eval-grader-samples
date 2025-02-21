// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

var uniqueId = uniqueString(resourceGroup().id)
var randomSuffix = substring(uniqueId, 0, 4)

@description('Specifies the name of the resource group.')
param resourceGroupName string
@description('Specifies the name of the deployment.')
param applicationName string
@description('Specifies the name of the deployment environment.')
param environment string
@description('Specifies the location of the Azure Machine Learning workspace and dependent resources.')
param location string = resourceGroup().location
@description('The username for the SQL Server admin')
param dbLoginUserName string
@secure()
@description('The password for the SQL Server admin')
param dbLoginPassword string
@description('Service Principal Object Id')
param servicePrincipalObjectId string
@description('Specifies the name of the ADLS Gen2 container 1')
param storageContainerOne string
@description('Specifies the name of the ADLS Gen2 container 1')
param storageContainerTwo string
@secure()
@description('Specifies the client secret for the ADLS Gen2 data store')
param clientSecret string
@description('Specifies the client ID for the ADLS Gen2 data store')
param clientId string
@description('Specifies the authority URL for the ADLS Gen2 data store')
param authorityUrl string
@description('Specifies the resource URL for the ADLS Gen2 data store')
param resourceUrl string
@description('Specifies the user principal ID')
param userPrincipalId string

var databaseName = 'db-${applicationName}-${environment}-${randomSuffix}'
var dbServerName = 'server-${applicationName}-${environment}-${randomSuffix}'
var blobStorageName = 'storage${applicationName}${environment}${randomSuffix}'


@description('Module for deploying storage resources such as ADLS Gen2 and SQL Server, Database')
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    container1Name: storageContainerOne
    container2Name: storageContainerTwo
    dbLoginUserName: dbLoginUserName
    dbLoginPassword: dbLoginPassword
    dbServerName: dbServerName
    databaseName: databaseName
    servicePrincipalObjectId: servicePrincipalObjectId
    blobStorageName: blobStorageName
  }
}

@description('Module for creating AML and related resources along with the role assignments')
module compute 'modules/compute.bicep' = {
  name: 'compute'
  params: {
    resourceGroupName: resourceGroupName
    applicationName: applicationName
    environment: environment
    location: location
    dbLoginUserName: dbLoginUserName
    dbLoginPassword: dbLoginPassword
    serverUrl: storage.outputs.serverUrl
    clientId: clientId
    clientSecret: clientSecret
    container1Name: storageContainerOne
    container2Name: storageContainerTwo
    authorityUrl: authorityUrl
    resourceUrl: resourceUrl 
    databaseName: databaseName
    userPrincipalId: userPrincipalId
    blobStorageName: blobStorageName
  }
}

@description('Module for creating observability resources such as Application Insights and Log Analytics Workspace')
module observability 'modules/observability.bicep' = {
  name: 'observability'
  params: {
    applicationName: applicationName
    environment: environment
    location: location
    logAnalyticsResourceId: compute.outputs.logAnalyticsResourceId
  }
}

@description('Module for creating OpenAI resources')
module openai 'modules/openai.bicep' = {
  name: 'openai'
  params: {
    location: location
    applicationName: applicationName
    environment: environment
    workspaceClusterPrincipalId: compute.outputs.workspaceClusterPrincipalId
  }
}
