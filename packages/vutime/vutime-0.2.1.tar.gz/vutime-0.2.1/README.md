# vutime

Time Based Utility Tools for Python

## Installation

```bash
pip install vutime
```

## Usage

### Adding Times

```python
from vutime import add_time

# Add two times in HH:MM:SS format
result = add_time("10:30:43", "07:53:49")
print(result)  # Output: 18:24:32

# Add times with different formats
result = add_time("10:30", "05:45", time_format_1="HH:MM", time_format_2="HH:MM", return_format="HH:MM:SS")
print(result)  # Output: 16:15:00
```

### Subtracting Times

```python
from vutime import subtract_time

# Subtract two times (time1 must be greater than time2)
result = subtract_time("10:30:43", "07:53:49")
print(result)  # Output: 02:36:54

# Subtract times with custom formats
result = subtract_time("10:30", "05:45", time_format_1="HH:MM", time_format_2="HH:MM")
print(result)  # Output: 04:45:00
```

### Getting Timezone Information

```python
from vutime.conversions.timezones import get_timezone

# Get timezone information for a specific identifier
tz_info = get_timezone("Asia/Tokyo")
print(tz_info)
# Output: {'identifier': 'Asia/Tokyo', 'sign': '+', 'offset': '09:00'}
```

### Converting Time Between Timezones

```python
from vutime.conversions.timezones import convert_time_tz

# Convert time from one timezone to another
result = convert_time_tz("12:00:00", "America/New_York", "Asia/Tokyo")
print(result)  # Output: 02:00:00 (next day)

# Convert with custom time formats
result = convert_time_tz("14:30", "Europe/London", "America/Los_Angeles", 
                        time_format="HH:MM", return_format="HH:MM")
print(result)  # Output: 06:30
```

## Format Options

Supported time formats:
- `HH:MM:SS` - Hours, minutes, seconds (default)
- `HH:MM` - Hours, minutes
- `MM:SS` - Minutes, seconds

## Supported Timezone Identifiers

The following is a complete list of all supported timezone identifiers (563 total):

Visit [List of all TZs](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) for a list of all timezone identifiers used.

## Requirements

- Python 3.12+

## License

MIT

