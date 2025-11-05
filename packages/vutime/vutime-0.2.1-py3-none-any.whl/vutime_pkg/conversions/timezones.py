import json
from retrieve_tzs import _retrieve_timezones
from datetime import datetime, date
from zoneinfo import ZoneInfo

try:
    with open("src/vutime_pkg/conversions/timezones.json", "r") as f:
        timezones = json.load(f)
except FileNotFoundError:
    timezones = _retrieve_timezones()
    if timezones is None:
        raise ValueError("Failed to retrieve timezones")
    else:
        with open("src/vutime_pkg/conversions/timezones.json", "r") as f:
            timezones = json.load(f)
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

def get_timezone(tz_identifier: str) -> str:
    return {
        "identifier": tz_identifier, 
        "sign": "+" if timezones.get(tz_identifier, None).startswith("+") else "-",
        "offset": timezones.get(tz_identifier, None).replace("+", "").replace("-", "")
        }

def convert_time_tz(time: str, tz_identifier_from: str, tz_identifier_to: str, 
                    time_format: str = "HH:MM:SS", return_format: str = "HH:MM:SS") -> str:
    """
    Convert a time string from one timezone to another using datetime and zoneinfo.
    
    Args:
        time: Time string in the format specified by time_format
        tz_identifier_from: Source timezone identifier (e.g., "America/New_York")
        tz_identifier_to: Target timezone identifier (e.g., "Asia/Tokyo")
        time_format: Format of the input time string (default: "HH:MM:SS")
        return_format: Format of the output time string (default: "HH:MM:SS")
    
    Returns:
        Time string in the target timezone
    
    Raises:
        ValueError: If timezone identifiers are invalid or time string format is invalid
    """
    # Validate timezone identifiers
    if tz_identifier_from not in timezones:
        raise ValueError(f"Invalid source timezone identifier: {tz_identifier_from}")
    if tz_identifier_to not in timezones:
        raise ValueError(f"Invalid target timezone identifier: {tz_identifier_to}")
    
    # Convert format strings
    time_format_python = _convert_format(time_format)
    return_format_python = _convert_format(return_format)
    
    # Parse the time string using today's date
    today = date.today()
    try:
        # Parse the time
        time_obj = datetime.strptime(time, time_format_python).time()
        # Create datetime object with today's date in the source timezone
        dt_from = datetime.combine(today, time_obj, tzinfo=ZoneInfo(tz_identifier_from))
    except ValueError as e:
        raise ValueError(f"Invalid time format or time string: {time}") from e
    
    # Convert to target timezone
    dt_to = dt_from.astimezone(ZoneInfo(tz_identifier_to))
    
    # Return time portion in the specified format
    return dt_to.strftime(return_format_python)

if __name__ == "__main__":
    print(convert_time_tz("10:30:43", "Pacific/Guam", "America/Nipigon"))