param name string = '\\"John Dole\\"'
param location string = resourceGroup().location

resource deploymentScript 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'inlinePS'
  location: location
  kind: 'AzurePowerShell'
  properties: {
    azPowerShellVersion: '10.0'
    arguments: '-name ${name}'
    scriptContent: '''
      param([string] $name)
      Write-Host 'The argument is {0}' -f $name
      $output = 'Hello {0}' -f $name
      $DeploymentScriptOutputs = @{}
      $DeploymentScriptOutputs['text'] = $output
    '''
    retentionInterval: 'PT1H'
  }
}

output result string = deploymentScript.properties.outputs.text