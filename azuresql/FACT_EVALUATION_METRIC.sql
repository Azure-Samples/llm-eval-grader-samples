Create table FACT_EVALUATION_METRIC(
metric_fact_id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
metric_id INT FOREIGN KEY(metric_id) REFERENCES DIM_METRIC(metric_id) NOT NULL,
evaluation_dataset_id INT NOT NULL,
app_id  INT NOT NULL,
conversation_id  INT NOT NULL,
metadata_id  INT NOT NULL,
evaluator_metadata Varchar(255),
metric_numeric_value INT,
metric_str_value Varchar(255),
metric_raw_value Varchar(255),
fact_creation_time DATETIME)