Create table FACT_EVALUATION_METRIC(
metric_fact_id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
metric_id INT FOREIGN KEY(metric_id) REFERENCES DIM_METRIC(metric_id) NOT NULL,
evaluation_dataset_id Varchar(255) NOT NULL,
conversation_id  Varchar(255),
metadata_id  Varchar(255),
evaluator_metadata Varchar(255),
metric_numeric_value FLOAT,
metric_str_value Varchar(255),
metric_raw_value Varchar(MAX),
fact_creation_time DATETIME
created_date DATETIME NOT NULL DEFAULT GETDATE(),
created_by VARCHAR(255) NOT NULL,
updated_date DATETIME NOT NULL DEFAULT GETDATE(),
updated_by VARCHAR(255) NOT NULL)