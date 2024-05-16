var uniqueId = uniqueString(resourceGroup().id)
var randomSuffix = substring(uniqueId, 0, 4)

@description('Specifies the name of the deployment.')
param applicationName string
@description('Specifies the name of the environment.')
param environment string
@description('Specifies the location of the Azure Machine Learning workspace and dependent resources.')
param location string
@description('Specifies the log analytics resource id')
param logAnalyticsResourceId string

var applicationInsightsName = '${applicationName}-${environment}-chatbot-logs-${randomSuffix}'


@description('Creates Application Insights resource for chaatbot logs')
resource resourceApplicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsResourceId
  }
}
