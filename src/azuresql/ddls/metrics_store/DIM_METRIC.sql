Create table DIM_METRIC(
metric_id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY, 
metric_name Varchar(255) NOT NULL,
metric_version Varchar(255) NOT NULL,
metric_type Varchar(255) NOT NULL,
evaluator_name Varchar(255) NOT NULL,
evaluator_type Varchar(255) NOT NULL)