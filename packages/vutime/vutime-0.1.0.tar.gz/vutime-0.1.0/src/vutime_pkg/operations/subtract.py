from datetime import datetime, timedelta

def _convert_format(format_str: str) -> str:
    """Convert custom format string (MM:SS, HH:MM:SS) to Python datetime format."""
    format_map = {
        "HH": "%H",
        "MM": "%M",
        "SS": "%S"
    }
    result = format_str
    for custom, python_format in format_map.items():
        result = result.replace(custom, python_format)
    return result


def _convert_to_timedelta(time: str, time_format: str) -> timedelta:
    """Convert a time string to a timedelta object"""
    python_format = _convert_format(time_format)
    return datetime.strptime(time, python_format).time()

def subtract_time(time1: str, time2: str, time_format_1: str = "HH:MM:SS", time_format_2: str = "", return_format: str = "HH:MM:SS") -> str:
    """
    Subtract two time strings together
    """
    
    
    time_format_1_python = _convert_format(time_format_1)
    time_format_2_python = _convert_format(time_format_2) if time_format_2 != "" else time_format_1_python
    return_format_python = _convert_format(return_format)
    
    #CHECK IF TIME1 IS GREATER THAN TIME2
    if _convert_to_timedelta(time1, time_format_1) < _convert_to_timedelta(time2, time_format_2 if time_format_2 != "" else time_format_1):
        raise ValueError("Time 1 must be greater than Time 2")
    
    # Parse times using a reference date to create datetime objects
    midnight = datetime(1900, 1, 1)
    time1_dt = datetime.strptime(time1, time_format_1_python).replace(
        year=1900, month=1, day=1)
    time2_dt = datetime.strptime(time2, time_format_2_python).replace(
        year=1900, month=1, day=1)
    
    # Convert to timedelta by calculating time since midnight
    delta1 = time1_dt - midnight
    delta2 = time2_dt - midnight
    
    # Subtract the timedeltas and convert back to time
    result_delta = delta1 - delta2
    result_dt = midnight + result_delta
    
    return result_dt.strftime(return_format_python)

if __name__ == "__main__":
    print(subtract_time("10:30:43", "07:53:49"))