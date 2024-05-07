import argparse
import ast
import datetime
from datetime import datetime, timezone
import pandas as pd

from llminspect.common.entities import AzureMonitorDataSource, MappingList
from llminspect.transformation.transform import DataTransformer
from llminspect.transformation.goldzone_prep import create_goldzone_tables
from llminspect.transformation.sampling import simple_sample


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
    
    # Create objects from the user arguments
    mapping_list = MappingList.from_dict(ast.literal_eval(args.mapping_list))
    data_source = AzureMonitorDataSource.from_dict(ast.literal_eval(args.data_source))
   
    # Converting the start_date and end_date to datetime with timezone
    start_date = datetime.strptime(args.start_date, "%Y/%m/%d").replace(tzinfo=timezone.utc)
    end_date = datetime.strptime(args.end_date, "%Y/%m/%d").replace(tzinfo=timezone.utc)
    
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

    # TODO: Read existing data
    existing_fact_data = pd.DataFrame()
    existing_metadata = pd.DataFrame()
    existing_conversation = pd.DataFrame()

    # Sampling the data
    concat_data = simple_sample(concat_data)

    # Prepare the data model
    fact_data, metadata, conversation = create_goldzone_tables(concat_data, existing_fact_data, existing_metadata, existing_conversation)

    # TODO: Write the data to the output paths


if __name__ == "__main__":
    main()