# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

#from azureml.core import Run
import mlflow

def mlflow_log_metric(metric_name, value):
    """Log custom metric through mlflow

    Args:
        metric_name (str): Name of the metric
        value (float): Value of the metric
    """
    mlflow.active_run()
    mlflow.log_metric(metric_name, value)

def mlflow_log_params(param_name, value):
    """Log custom parameter through mlflow

    Args:
        param_name (str): Name of the parameter
        value (float): Value of the parameter
    """
    mlflow.active_run()
    mlflow.log_param(param_name, value)
