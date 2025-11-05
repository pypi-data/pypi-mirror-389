import requests
import os
from bs4 import BeautifulSoup
import json


def _get_timezones():
    """Get all timezones from the website"""
    url = "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the timezone table - class is "wikitable sortable sticky-header-multi" (without jquery-tablesorter)
    table = soup.select_one("table.wikitable.sortable.sticky-header-multi")
    
    if table is None:
        raise ValueError("Could not find the timezone table on the Wikipedia page")
    
    tbody = table.find("tbody")
    if tbody is None:
        # Some tables don't have tbody, try finding tr directly in table
        regions = table.find_all("tr")
    else:
        regions = tbody.find_all("tr")
    
    # Skip header rows (first two rows contain <th> elements, not <td>)
    data_rows = [row for row in regions if row.find("td") is not None]
    
    print(f"Found {len(data_rows)} timezone regions")
    timezone_dict = {}
    for row in data_rows:
        tds = row.find_all("td")
        if len(tds) >= 5:
            tz_identifier = tds[1].text.strip()
            if tz_identifier.startswith("Etc/"):
                continue
            tz_offset = tds[4].text.strip()
            timezone_dict[tz_identifier] = tz_offset
    return timezone_dict

def _retrieve_timezones():
    timezones = _get_timezones()
    try:
        with open("src/vutime_pkg/conversions/timezones.json", "w") as f:
            json.dump(timezones, f, indent=4)

        with open("src/vutime_pkg/conversions/timezones.json", "r") as f:
            data = json.load(f)
            for key, value in data.items():
                if value.startswith("+"):
                    continue
                elif value.startswith("\u2212"):
                    data[key] = value.replace("\u2212", "-")
                else:
                    data[key] = value
        with open("src/vutime_pkg/conversions/timezones.json", "w") as f:
            json.dump(data, f, indent=4)
        return data

    except FileNotFoundError as e:
        print(f"File not found: {e}.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
