import requests
import pandas as pd
from typing import Optional, Dict

def fetch_api_data(api_url: str, params: Optional[Dict] = None, data_key: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch JSON data from API and convert it to pandas DataFrame.
    """
    response = requests.get(api_url, params=params)
    response.raise_for_status()
    data = response.json()

    # If the API returns nested JSON (e.g., hourly/daily)
    if data_key and data_key in data:
        data = data[data_key]

    df = pd.DataFrame(data)
    return df
