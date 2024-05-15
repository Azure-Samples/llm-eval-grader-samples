from datetime import datetime,timedelta


def get_datetime_from_date_str(date_str: str) -> datetime:
    """Get datetime from date string

    Args:
        date_str (string): date string in format YYYY/MM/DD HH:MM

    Returns:
        datetime: datetime object
    """
    return datetime.strptime(date_str, "%Y/%m/%d %H:%M")

def time_range_for_scheduling():
    """
    Calculate the time range for scheduling a pipeline run.
    
    Returns:
        tuple: A tuple containing the second last Sunday and the last Saturday.
    """
    pipeline_run_day = datetime.today()
    last_saturday = pipeline_run_day - timedelta(days=(pipeline_run_day.weekday() + 2) % 7)
    second_last_sunday = last_saturday - timedelta(days=6)
    return second_last_sunday, last_saturday

def start_date_for_pipeline_run(start_date: str) -> datetime:
    """
    Converts the start date string to a datetime object.
    
    Args:
        start_date (str): The start date in the format "YYYY/MM/DD HH:MM".
        
    Returns:
        datetime: The converted datetime object.
    """
    second_last_sunday, _ = time_range_for_scheduling()
    return datetime.combine(second_last_sunday, datetime.min.time()) if start_date.strip() == "NA" else datetime.strptime(start_date, "%Y/%m/%d %H:%M")
  
def end_date_for_pipeline_run(end_date:str) -> datetime:
    """_summary_

    Args:
        end_date (str): _description_

    Returns:
        _type_: _description_
    """    
    _, last_saturday = time_range_for_scheduling()
    return datetime.combine(last_saturday, datetime.max.time()) if end_date.strip() == "NA" else datetime.strptime(end_date, "%Y/%m/%d %H:%M")