Create table DIM_CONVERSATION(
conversation_id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY, 
conv_start_time DATETIME,
conv_end_time DATETIME)