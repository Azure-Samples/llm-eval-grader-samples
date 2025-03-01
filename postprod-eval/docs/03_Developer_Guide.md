# Developer Guide

This document provides a guide for developers on how to build the following components of the evaluation framework:

- Prompt flows for evaluation
- Azure Machine Learning (AML) pipelines for orchestration
- Power BI dashboards for visualization

## Development Environment Setup

Step 1: Install Visual Studio Code with the following extensions:  
     - Prompt Flow  
Step 2:  Create `.env` file from [`.env_template`](../azureml/pipeline/deploy/env.template)and update the values as per your Azure environment.  
Step 3:  Install the Azure CLI and login to your Azure account:  
``` bash
az login
```
Note: If you get login issues, retry the command after you login to azure portal(`portal.azure.com`) from browser.

### Conda Environment Setup
Create a new Python environment with required libraries and activate it:

``` bash
cd src\azureml\pipeline

conda create --name <ENVIRONMENT_NAME> python=3.10
conda activate <ENVIRONMENT_NAME>

pip install -r requirements.txt
```

## Development of Prompt Flow

Prompt flow is used to evaluate the performance of the chat bot. When a new evaluation metric is added to the evaluation framework, a new prompt flow must be developed to generate the metric.

### Steps

1. Define the new metric in the [evaluation_config.yml](../azureml/pipeline/config/evaluation_config.yml) file.
2. Develop the prompt flow in a new folder under [`azureml/promptflow/`](../azureml/promptflow/). The name of the folder represents the name of metric that will be generated.
3. Use one of the existing prompt flows as a template to develop the new prompt flow. You can refer to [turn_relevance prompt flow](../azureml/promptflow/turn_relevance/) to develop a basic prompt flow that generates a single metric.
4. Update the jinja templates in the prompt flow to define the evaluation criteria. Ensure that the metric names defined in the jinja templates match the metric names defined in the evaluation_config.yml.
5. Update the `samples.jsonl` file with the sample data required to evaluate the metric.
6. Update the `parse_input.py` file with custom logic to parse the input data, if required. For most scenarios, the default logic provided in the template should be sufficient. The `evaluation_dataset` input variable contains all the fields from fact evaluation dataset that are required to evaluate the metric.
7. Update the `parse_score.py` file with custom logic to parse LLM output. As part of this step, the following fields are generated as the evaluation output:

    - metric_name - as defined in the evaluation_config.yml
    - metric_version - as defined in the evaluation_config.yml
    - metric_value - the value of the metric after parsing LLM output
    - metric_raw_value - the raw LLM output

8. Write unit test cases for `parse_score.py` and add the unit test case execution in the git pre-commit hook file as follows:

    ```bash
        python -m unittest discover -s ./azureml/promptflow/<PROMPT_FLOW_NAME_FOLDER>
    ```

9. Test the prompt flow locally using the Visual Studio Code prompt flow extension. Refer to the [this documention](https://learn.microsoft.com/en-us/semantic-kernel/agents/planners/evaluate-and-deploy-planners/running-batches-with-prompt-flow?tabs=gpt-35-turbo#use-the-visual-editor-to-run-a-batch-of-inputs) for detailed steps. Alternatively, you can test using Prompt Flow SDK referring to the steps [here](../../src/azureml/promptflow/e2e_answerability/README.md).
10. Once the prompt flow is developed and tested, update the `flow_path` property with the `flow.dag.yaml` path of the prompt flow in the [evaluation_config.yml](../azureml/pipeline/config/evaluation_config.yml) file for the specific evaluator.

### Run the Flow in local/azure Pipeline

Now execute the flow in visual studio code or in Azure AI/ML studio Pipeline by running the LLM evaluation pipeline. Please take help from the [promptflow official documentation](https://microsoft.github.io/promptflow/how-to-guides/quick-start.html#develop-and-test-your-flow).

## Development of Azure Machine Learning (AML) Pipelines

### Data Transformation Pipelines

Data transformation pipelines are used to transform the raw data into a format that can be used for evaluation.

- Source: Azure Monitor Logs
- Destination: Parquet files in Azure Data Lake Storage (ADLS) Gen 2 (gold zone)

#### Steps to Develop Data Transformation Pipelines

1. To develop a new transformation pipeline for a new app, define the following in the [transformation_config.yml](../azureml/pipeline/config/transformation_config.yml) file:

    - Update the chatbot_name as per the name of your chatbotname: transformation
    chatbot_name: sample-chatbot
    - Update the source which has 
    source:
        - type: type of data source, in our case, azure monitor
        - table: table name in Azure monitor
        - workspace_id_secret_key: the key in the keyvault storing the secret value of workspace_id of the log analytic workspace, this might be applicable when the type is azure monitor, but not otherwise.(eg, Azure SQL)
    - Update the mapping between source and target table columns for conversation and llm separately
    - Define transformation specific AML pipeline configurations such as endpoint, schedule, schedule start time etc.

2. The transformation pipeline source code is at two places, one in the azureml folder, other in the src folder.
    - [transform_data.py](../azureml/pipeline/components/code/transform_data.py) This acts like the onboarding script for transformation.It imports the code in the src/llmevalgrader folder, calling the common and transformation folder. This script orchestrates the transformation process. It calls the respective code which reads the data from azure monitor, transforms the data, as per mappings specified in the transfromation_config file , samples it and updates the dim and fact tables in the ADLS Gen2 (GOLD ZONE) in parquet format. It will create the dim_conversation, dim_metadata, fact_evaluation output files if not present , or update them if already present. Finally clean data is stored in the GOLD ZONE, ready for evaluation pipeleines
    - [transformation.yml](../azureml/pipeline/components/definition/transformation.yml) This file has the definition for the transformation component. It has the input and outputs defined and the conda environment to be created.
    - [deploy_transformation_pipeline.py](../azureml/pipeline/deploy/deploy_transformation_pipeline.py)
        This file is the actual deploy script which invokes the transform_data.py
    - The common reusable code is located in the  [src/llmevalgrader/common/](../src/llmevalgrader/common/)  and [src/llmevalgrader/transformation/](../src/llmevalgrader/transformation/) which is packaged and imported in the [src/azureml/pipeline/components/code/](../azureml/pipeline/components/code) python scripts
        - [transform.py](../src/llmevalgrader/transformation/transform.py)
        This file does all the main transformations in the data at the bot and the component level. If there is a change in the data format, data schema or transformation logic, one needs to make the changes here in the corresponding functions. Currently this file is specific to sample chatbot application. This file takes care of reading the data from azure monitor and mapping the columns and do the preprocessing on the data.
        - [goldzone_prep.py](../src/llmevalgrader/transformation/goldzone_prep.py)
        This file reads and updates the goldzone table, namely the dim_metadata,dim_conversation and fact_evaluation_dataset
        - [sampling.py](../src/llmevalgrader/transformation/sampling.py) This python script takes care of checking unique sessions and taking a fraction of these to be sampled and used for transformation pipeline, which gets written to the gold zone and finally is used by the eval pipeline

### LLM Evaluation Pipelines

Evaluation pipelines are used to orchestrate the evaluation process. The evaluation pipeline reads data from ADLS Gen2, runs evaluation prompt flow against this data and writes the metrics generated to Azure SQL.

#### Steps to Develop LLM Evaluation Pipelines

1. To develop a new evaluation pipeline for a new bot or component, define the following in the [evaluation_config.yml](../azureml/pipeline/config/evaluation_config.yml) file:

    - Define the new bot in the "app" section.
    - List the evaluators to be run for the bot or component. This must match the evaluators defined in the "evaluators" section.
    - Define evaluator specific AML pipeline configurations such as endpoint, schedule, schedule start time etc.
2. The evaluation pipeline source code is generic and can be used for any bot or component. The source code is located in the [azureml/pipeline/components/code/](../azureml/pipeline/components/code) folder. The source code is comprised of two main scripts:

    1. [prep_data.py](../azureml/pipeline/components/code/prep_data.py) - Prep Data Component
        - This script filters source data in ADLS Gen 2 gold zone based on the supplied start and end date parameters. For scheduled pipelines, the start and end date parameters are set as default to the previous day's date. If required, the default logic can be updated to filter data based on a different date range in the `main` method. For pipeline invokation via batch endpoint, the start and end date parameters are supplied as input to the pipeline and it overrides the default logic.
    1. [write_metrics.py](../azureml/pipeline/components/code/write_metrics.py) - Write Metrics Component
        - This script writes the metrics generated by the prompt flow to Azure SQL database table [FACT_EVALUATION_METRIC](../azuresql/FACT_EVALUATION_METRIC.sql).

## Development of Power BI Dashboards

1. Install Power BI Desktop (supports only Windows)
    1. In case of Mac, one can use Windows Virtual Machine or use Power BI Service (limited capabilities) for report development
1. Download the Power BI Semantic Model `LLM_Inspector` (PBIX) file from the [this location](../dashboards/LLM_Inspector.pbix)
1. Open the PBIX file in Power BI Desktop and update the following data source credentials as per your Azure environment
    1. ADLS Gen2 Storage Account Key
    1. Azure SQL Database Server Name and Username/Password
1. Refresh the data and update the report visuals
1. Update the report visuals and publish the report to the Power BI Service
1. Validate the scheduled refresh of the report in the Power BI Service

## Testing and Debugging

### Testing Azure Machine Learning (AML) Pipelines

1. Once the prompt flow and AML pipelines are developed, deploy the AML pipelines by following the [deployment guide](./02_Deployment.md).
1. Batch endpoints are used for testing the AML pipelines manually. Trigger a manual run of the AML pipeline by following the steps mentioned in the [deployment guide](./02_Deployment.md#run-pipelines-manually).

### Debugging Azure Machine Learning (AML) Pipelines

Each component of a pipeline run has it's own logs. To view the logs, go to the aml workspace and specific pipeline, double click on the pipeline component > click on "Outputs + logs" tab.
1. Logs from pipeline source code can be found under `user_logs` > `std_log.txt`
1. Data outputs from a pipeline run can be found under `Data Outputs` > `Show data outputs` > click `Preview data` to view the data
1. For evaluation pipelines, errors with prompt flow execution can be found under `logs` > `job_error.<CURRENT_DATE>.txt`.
1. For evaluation pipelines, details of prompt flow mini-batch executions can be found under `logs` > `sys` > `job_report` folder


### Debugging issues related to SQL Server

The framework uses Azure Serverless SQL Server model for two purposes:

1. Chatbot Evaluation Process being batched
2. Cost benefits.

Azure Serverless [may experience a delay](https://learn.microsoft.com/en-us/azure/azure-sql/database/serverless-tier-overview?view=azuresql&tabs=general-purpose) in resuming from a paused state, which is known as a cold start. The duration of the cold start depends on the size and state of the database, and the workload characteristics.

Typical issues are listed below -

- SQL Server is unavailable for a long time due to global infrastructure problems such as network failure or regional outage.
- SQL Server password has expired
- Azure SQL Server takes too long to resume from the paused state.

If you encounter any of these errors or similar ones, you may see the following error message. Please check the StdError logs in the Pipeline Monitor to identify and resolve the error before running the pipeline manually or through Schedule.

```text
2024-02-19 07:19:19,251 - db_handler - ERROR - Error connecting to database: ('HYT00', '[HYT00] [Microsoft][ODBC Driver 17 for SQL Server]Login timeout expired (0) (SQLDriverConnect)')
Traceback (most recent call last):
  File "/mnt/azureml/cr/j/a4b649d27bde4cdda57b9fa9a98edb09/exe/wd/common/db_handler.py", line 40, in init_db_connection
    self.conn = pyodbc.connect(conn_str, timeout=300)
pyodbc.OperationalError: ('HYT00', '[HYT00] [Microsoft][ODBC Driver 17 for SQL Server]Login timeout expired (0) (SQLDriverConnect)')
Traceback (most recent call last):
  File "/mnt/azureml/cr/j/a4b649d27bde4cdda57b9fa9a98edb09/exe/wd/write_metrics.py", line 167, in <module>
    main()
  File "/mnt/azureml/cr/j/a4b649d27bde4cdda57b9fa9a98edb09/exe/wd/write_metrics.py", line 159, in main
    metrics_processor = MetricsProcessor(args.key_vault_url)
  File "/mnt/azureml/cr/j/a4b649d27bde4cdda57b9fa9a98edb09/exe/wd/write_metrics.py", line 21, in __init__
    self.db_handler.init_db_connection()
  File "/mnt/azureml/cr/j/a4b649d27bde4cdda57b9fa9a98edb09/exe/wd/common/db_handler.py", line 40, in init_db_connection
    self.conn = pyodbc.connect(conn_str, timeout=300)
pyodbc.OperationalError: ('HYT00', '[HYT00] [Microsoft][ODBC Driver 17 for SQL Server]Login timeout expired (0) (SQLDriverConnect)')

```

### Data Validation

1. Data transformation pipeline

- Parquet files are created in the gold zone in the right date partitions as per the input date range.

```python
gold-zone/fact_evaluation_dataset/fact_evaluation_dataset/year=YYYY/month=M/day=D/*.parquet
```

- Use the [Jupyter notebook](../notebooks/client.ipynb) to read the parquet file via pandas and verify the data.

1. Evaluation pipeline

- Query the table `FACT_EVALUATION_METRIC` in the Azure SQL database to verify that evaluation metrics are loaded.

```sql
SELECT TOP 10 D.METRIC_NAME, F.*
FROM [dbo].[FACT_EVALUATION_METRIC] F
INNER JOIN
[dbo].[DIM_METRIC] D
ON F.METRIC_ID = D.METRIC_ID
WHERE D.METRIC_NAME = 'turn_relevance' AND D.METRIC_VERSION = 1.0
```
