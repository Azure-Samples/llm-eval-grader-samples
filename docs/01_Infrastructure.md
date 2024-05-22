# Infrastructure Deployment

The infrastructure deployment process involves executing Bicep scripts located in the infra folder. These scripts are organized into modules and executed sequentially due to dependencies between them.

## Storage Module
- Provisioning of SQL Server with a database.
- Creation of ADLS Gen2 with specified containers.
- Assignment of RBAC roles.
## Compute Module
- Setup of ADLS Gen2 Storage account.
- Creation of Log Analytics Workspace.
- Creation and Configuration of Application Insights.
- Deployment of Keyvault with secrets.
- Creation of AML Workspace and compute cluster.
- Configuration of Datastore for ADLS Gen2 containers.
- Assignment of RBAC roles.
## Observability Module
- Creation and Configuration of Application Insights
- Assignment of RBAC roles.
## OpenAI Module
- Deployment of OpenAI Cognitive Service and Models.
- Assignment of RBAC roles
- Note: Currently, `ms.default` is utilized for raiPolicy which could be enhanced for detailed RAI configs 

## Deployment Details

### Prerequisites
1. Check and create the resource group if it doesn't exist.
2. Create a Service Principal if it's not available.

### Step 1:Define Parameters
Define user parameters required for deployment in the [parameters.json](../infra/parameters.json) file. Adjust values as necessary.

### Step 2:Set environment variables
Sensitive information like `client_id`, `client_secret`, etc., should be set as environment variables. Refer to [.env.template](../infra/modules/env.template) and populate the values as required.

### Step 3:Validate script
Build the Bicep script and ensure there are no syntax errors:
` bicep build main.bicep`

### Step 4:Run Bicep Script
Execute the Bicep script using the following command:
``` 
az deployment group create --name llmops-infra-deployment --resource-group <resource group name> --template-file main.bicep --parameters parameters.json --parameters clientId=CLIENT_ID --parameters clientSecret=CLIENT_SECRET --parameters dbLoginUserName=DB_LOGIN_USERNAME --parameters dbLoginPassword=DB_LOGIN_PASSWORD 
```
Monitor deployment progress in the Azure Portal under the `Deployments` pane in `Settings` of the `Resource groups` section.

### Step 5:Create Open AI Promptflow connection
1. Navigate to the AML Workspace and click on `promptflow` -> `connections`.
2. Create an Open AI connection, filling in the necessary details from OpenAI.
Ensure the connection name is `azure_open_ai_connection` as referenced in the source code.

### Step 6:Run DDL SQL Scripts
1. Access the SQL Database and open Query Editor.
2. Execute the content from SQL files located under the `azuresql` folder in the source code.
3. Verify successful creation of `DIM_METRIC` and `FACT_EVALUATION_METRIC` tables.

## Troubleshooting

### Character Limit
Ensure that values provided in parameter.json for applicationName and environment comply with character limits, as many Azure resources have constraints, e.g., Storage account name.

### Database Firewall issue
The infrastructure script manages Azure internal traffic to the SQL database by whitelisting IPs. However, in edge cases where compute nodes in the cluster have IPs outside the specified range, consider scaling down and then up the nodes in the cluster.
