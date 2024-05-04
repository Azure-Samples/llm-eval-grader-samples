Create table FACT_EVALUATION_DATASET(
evaluation_dataset_id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY, 
conversation_id INT FOREIGN KEY(conversation_id) REFERENCES DIM_CONVERSATION(conversation_id) NOT NULL,
metadata_id INT FOREIGN KEY(metadata_id) REFERENCES DIM_METADATA(metadata_id) NOT NULL,
turn_id INT,
response text,
context text,
query text)