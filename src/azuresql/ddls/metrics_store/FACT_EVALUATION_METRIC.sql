Create table FACT_EVALUATION_METRIC(
metric_fact_id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY,
evaluation_dataset_id INT FOREIGN KEY(evaluation_dataset_id) REFERENCES FACT_EVALUATION_DATASET(evaluation_dataset_id) NOT NULL,
app_id INT FOREIGN KEY(app_id) REFERENCES DIM_APPLICATION(app_id) NOT NULL,
conversation_id INT FOREIGN KEY(conversation_id) REFERENCES DIM_CONVERSATION(conversation_id) NOT NULL,
metadata_id INT FOREIGN KEY(metadata_id) REFERENCES DIM_METADATA(metadata_id) NOT NULL,
evaluator_metadata Varchar(255),
metric_numeric_value INT,
metric_str_value Varchar(255),
metric_raw_value Varchar(255),
conv_start_time DATETIME)