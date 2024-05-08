import argparse
import ast
import datetime
from datetime import datetime, timezone, timedelta
import pandas as pd


from llminspect.common.entities import AzureMonitorDataSource, MappingList
from llminspect.transformation.transform import DataTransformer
from llminspect.transformation.goldzone_prep import create_goldzone_tables
from llminspect.transformation.sampling import simple_sample
from llminspect.common.adls_handler import ADLSHandler
from llminspect.common.logger import get_logger


def parse_args():
    """
    Parses the user arguments.

    Returns:
        argparse.Namespace: The parsed user arguments.
    """
    parser = argparse.ArgumentParser(
        allow_abbrev=False, description="parse user arguments"
    )
    parser.add_argument("--chatbot_name", type=str, help="Chatbot name", required=True)
    parser.add_argument("--data_source", type=str, help="Data source", required=True)
    parser.add_argument("--mapping_list", type=str, help="Columns to be selected", required=True)
    parser.add_argument("--start_date", type=str, help="Start date", required=True)
    parser.add_argument("--end_date", type=str, help="End date", required=True)
    parser.add_argument("--key_vault_url", type=str, help="Key vault url", required=True)
    parser.add_argument("--fact_evaluation_output", type=str, help="Fact evaluation output path", required=True)
    parser.add_argument("--dim_metadata_output", type=str, help="Dim metadata output path", required=True)
    parser.add_argument("--dim_conversation_output", type=str, help="Dim sessions output path", required=True)
    args, _ = parser.parse_known_args()
    return args

def main():
    args = parse_args()
    logger = get_logger("transform_data")
    
    # Create objects from the user arguments
    mapping_list = MappingList.from_dict(ast.literal_eval(args.mapping_list))
    data_source = AzureMonitorDataSource.from_dict(ast.literal_eval(args.data_source))
   
    
    
    pipeline_run_day = datetime.today()
    tomorrow = pipeline_run_day + timedelta(days=1)
    start_date_default = tomorrow - timedelta(days=6)
    start_date = datetime.combine(start_date_default, datetime.min.time()) if args.start_date.strip() == "NA" else datetime.strptime(args.start_date, "%Y/%m/%d") 
    end_date =  datetime.combine(tomorrow, datetime.max.time()) if args.end_date.strip() == "NA" else datetime.strptime(args.end_date, "%Y/%m/%d")
    logger.info(f"Start Date is {start_date.strftime('%m/%d/%Y')}")
    logger.info(f"End Date is {end_date.strftime('%m/%d/%Y')}")

    
    # Initialize the transformation processor
    transformation_processor = DataTransformer(
        start_date=start_date,
        end_date=end_date,
        key_vault_url=args.key_vault_url,
        data_source=data_source,
        mappings=mapping_list,
    )

    # Orchestrating the transformation process
    transformation_dtos = transformation_processor.get_logs()
    transformation_dtos = transformation_processor.transform_data(transformation_dtos)
    transformation_dtos = transformation_processor.clean_data(transformation_dtos)
    transformation_dtos = transformation_processor.add_optional_extra_columns(transformation_dtos,
                                                                              "chatbot_name", args.chatbot_name)
    concat_data = transformation_processor.concat_data(transformation_dtos)
    concat_data = transformation_processor.fill_missing_values(concat_data)

    # Read existing data
    adls_handler = ADLSHandler()
    try:
        existing_fact_data = adls_handler.read_fact_table(
            fact_output_path=args.fact_evaluation_output, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        logger.warning(f"Failed to read existing fact data from path {args.fact_evaluation_output} : {e}")
        logger.info("Creating new fact data")
        existing_fact_data = pd.DataFrame()
    try:
        existing_metadata = adls_handler.read_dim_table(
            dim_output_path=args.dim_metadata_output, dim_file_name="dim_metadata.parquet"
        )
    except Exception as e:
        logger.warning(f"Failed to read existing dim metadata from path {args.dim_metadata_output} : {e}")
        logger.info("Creating new metadata")
        existing_metadata = pd.DataFrame()
    try:
        existing_conversation = adls_handler.read_dim_table(
            dim_output_path=args.dim_conversation_output, dim_file_name="dim_conversation.parquet"
        )
    except Exception as e:
        logger.warning(f"Failed to read existing dim conversation from path {args.dim_conversation_output} : {e}")
        logger.info("Creating new conversation")
        existing_conversation = pd.DataFrame()

    # Sampling the data
    concat_data = simple_sample(concat_data)

    # Prepare the data model
    fact_data, metadata, conversation = create_goldzone_tables(concat_data, existing_fact_data, existing_metadata, existing_conversation)
    logger.info("Data model created successfully")
    logger.info(f"New Fact data shape: {fact_data.shape}")
    logger.info(f"New Metadata shape: {metadata.shape}")
    logger.info(f"New Conversation shape: {conversation.shape}")

    # Write the data to the output paths
    logger.info("Writing data to output paths")
    adls_handler.write_fact_table(args.fact_evaluation_output, fact_data)
    adls_handler.write_dim_table(
        args.dim_metadata_output,
        "dim_metadata.parquet",
        metadata,
    )
    adls_handler.write_dim_table(
        args.dim_conversation_output,
        "dim_conversation.parquet",
        conversation,
    )
    logger.info("Data written successfully")
    logger.info("Data transformation completed")


if __name__ == "__main__":
    main()