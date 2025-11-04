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

## Format Options

Supported time formats:
- `HH:MM:SS` - Hours, minutes, seconds (default)
- `HH:MM` - Hours, minutes
- `MM:SS` - Minutes, seconds

## Requirements

- Python 3.12+

## License

MIT

