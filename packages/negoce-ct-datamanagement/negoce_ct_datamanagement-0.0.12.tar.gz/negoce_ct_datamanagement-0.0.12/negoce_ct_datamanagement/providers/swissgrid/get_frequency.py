import requests
import datetime
import pandas as pd
import os

def fetch_and_save_frequency_data(url="https://data.swissgrid.ch/charts/frequency/?lang=en", data_dir="Data/frequency"):
    """
    Fetch frequency data from the given URL, process it, and save it as a Parquet file.

    Parameters:
    - url (str): The URL to fetch the frequency data from.
    - data_dir (str): The directory where the Parquet file will be saved.

    Returns:
    - str: The file path of the saved Parquet file.
    """
    # Fetch the JSON
    response = requests.get(url)
    response.raise_for_status()  # Raise an error if the request fails
    data = response.json()

    # Extract the list of [timestamp, frequency] pairs
    series_data = data["data"]["series"][0]["data"]

    # Convert to DataFrame
    df = pd.DataFrame(series_data, columns=["timestamp_ms", "frequency"])
    df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit='ms')
    df = df[["timestamp", "frequency"]]

    # Optional: sort by timestamp just in case
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Generate file name
    file_name = f'swissgrid_frequency_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.parquet'

    # Ensure the directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Save to Parquet
    file_path = os.path.join(data_dir, file_name)
    df.to_parquet(file_path, index=False)

    print("File saved to:", file_path)
    print("File name is:", file_name)
    print("Data is :", df.head())

    return df