from typing import List, Optional, Literal
from datetime import datetime, timedelta, date
from negoce_ct_datamanagement.providers.volue._config import VolueApi
import pandas as pd
from requests import HTTPError
import os
import json
import glob
from pathlib import Path


def get_latest_curves(curves_id: List[int], date_from: datetime, date_to: datetime) -> list:
    """
        Get list of curves data for a time range
    :param curves_id: (List[int]) list of curves id to get data from
    :param date_from: (datetime)
    :param date_to: (datetime)
    :return: list of requested curves objects
    """
    # build request
    date_from = date_from.strftime("%Y-%m-%d")
    date_to = date_to.strftime("%Y-%m-%d")

    data = []
    for curve_id in curves_id:
        url = f'instances/{curve_id}/latest?data_from={date_from}&data_to={date_to}'
        # query and get results
        vapi = VolueApi()
        data.append(vapi.send_request(url))
    return data

def get_curves(curves_id: List[int], date_from: datetime, date_to: datetime, issue_date: datetime) -> list:
    """
        Get list of curves data for a time range
    :param curves_id: (List[int]) list of curves id to get data from
    :param date_from: (datetime) start date of the forecast
    :param date_to: (datetime) end date of the forecast
    :param issue_date: (datetime) date of the forecast
    :return: list of requested curves objects
    """
    # build request
    date_from = date_from.strftime("%Y-%m-%d")
    date_to = date_to.strftime("%Y-%m-%d")
    issue_date = issue_date.strftime("%Y-%m-%d")

    data = []
    for curve_id in curves_id:
        url = (
            f"instances/{curve_id}/get"
            f"?issue_date={issue_date}"
            f"&from={date_from}"
            f"&to={date_to}"
        )        # query and get results
        vapi = VolueApi()
        data.append(vapi.send_request(url))
    return data

def retrieve_forecasts_incremental(
    curve_ids: list[int],
    start_date: datetime,
    end_date: datetime,
    nb_days_ahead: int,
    nb_days_forecast: int,
    data_name: str,
    data_path: str,
    previously_fetched_data: dict = None,
) -> tuple:
    """
    Retrieves forecast curves from Volue for each day between start_date and end_date (inclusive),
    using the function get_curves() and only fetching what hasn't been retrieved before.
    Data is cached in parquet files in the Data/{data_name} directory.
    
    :param curve_ids:           List of curve IDs to query (e.g. [24959])
    :param start_date:          Start of the main date range
    :param end_date:            End of the main date range (inclusive)
    :param nb_days_ahead:       Number of days ahead (typically 1 for day-ahead)
    :param nb_days_forecast:    Forecast horizon (days after the 'issue date')
    :param previously_fetched_data: Dictionary with previously fetched data
    :param data_name:           Name of the data folder inside the Data directory
    :param data_path:           Folder to save data in
    
    :return: A tuple containing:
             1. A list of raw curve objects (one entry per successful day)
             2. The updated cache dictionary containing all data
    """


    # Ensure the data directory exists
    data_dir = os.path.join(data_path, data_name)
    cache_index_path = os.path.join(data_dir, "cache_index.parquet")
    os.makedirs(data_dir, exist_ok=True)

    # Load cache index or create a new one
    cache = {}
    if previously_fetched_data is None:
        if os.path.exists(cache_index_path):
            try:
                cache_df = pd.read_parquet(cache_index_path)
                # Convert DataFrame to dictionary
                for _, row in cache_df.iterrows():
                    cache[row['cache_key']] = row['file_path']
                print(f"Loaded cache index with {len(cache)} entries from {cache_index_path}")
            except Exception as e:
                print(f"Error loading cache index: {e}")
                cache = {}
    else:
        cache = previously_fetched_data.copy()

    # Generate the daily date range
    date_list = [
        start_date + timedelta(days=x)
        for x in range((end_date - start_date).days + 1)
    ]

    curves = []
    new_data_fetched = False
    new_cache_entries = []

    for date_issued in date_list:
        # 'forecast' is from date_issued+1 to date_issued+nb_days_forecast
        from_date = date_issued + timedelta(days=nb_days_ahead)
        to_date = date_issued + timedelta(days=nb_days_forecast)

        # Create a cache key for this specific request
        cache_key = f"{'-'.join(map(str, curve_ids))}_{date_issued.strftime('%Y-%m-%d')}_" \
                   f"{from_date.strftime('%Y-%m-%d')}_{to_date.strftime('%Y-%m-%d')}"

        # Check if we already have this data
        if cache_key in cache:
            file_path = cache[cache_key]
            if os.path.exists(file_path):
                print(f"✓ Using cached data for issue_date={date_issued}")
                with open(file_path, 'r') as f:
                    curves_data = json.load(f)
                curves.append(curves_data)
                continue

        # If not in cache or file missing, retrieve from API
        try:
            print(f"⏳ Fetching new data for issue_date={date_issued}")
            curves_data = get_curves(curve_ids, from_date, to_date, date_issued)
            new_data_fetched = True

            # Generate unique filename for this data
            file_name = f"forecast_{'-'.join(map(str, curve_ids))}_{date_issued.strftime('%Y%m%d')}.json"
            file_path = os.path.join(data_dir, file_name)

            # Save data to JSON file
            with open(file_path, 'w') as f:
                json.dump(curves_data, f)

            # Update cache entry
            cache[cache_key] = file_path
            new_cache_entries.append({
                'cache_key': cache_key,
                'file_path': file_path,
                'curve_ids': '-'.join(map(str, curve_ids)),
                'issue_date': date_issued.strftime('%Y-%m-%d'),
                'from_date': from_date.strftime('%Y-%m-%d'),
                'to_date': to_date.strftime('%Y-%m-%d')
            })

            curves.append(curves_data)

        except HTTPError as ex:
            if ex.response.status_code == 404:
                # Means no forecast for that date/horizon
                print(f"⚠️ No forecast found for issue_date={date_issued}, skipping.")
                continue
            else:
                # Other HTTP errors should be re-raised
                raise

    # Save updated cache index if new data was fetched
    if new_data_fetched:
        try:
            # Create or update the cache index DataFrame
            if new_cache_entries:
                new_entries_df = pd.DataFrame(new_cache_entries)
                if os.path.exists(cache_index_path):
                    existing_df = pd.read_parquet(cache_index_path)
                    updated_df = pd.concat([existing_df, new_entries_df], ignore_index=True)
                else:
                    updated_df = new_entries_df

                # Save as parquet
                updated_df.to_parquet(cache_index_path, index=False)
                print(f"✓ Cache index updated and saved to {cache_index_path}")
        except Exception as e:
            print(f"⚠️ Error saving cache index: {e}")

    return curves, cache

def load_and_merge_forecast_data(
    curve_ids: list[int],
    start_date: datetime,
    end_date: datetime,
    nb_days_ahead: int,
    nb_days_forecast: int ,
    data_name: str,
    data_path: str
) -> dict:
    """
    Loads previously fetched data, fetches any missing data, 
    and returns parsed DataFrames for each curve.
    
    :param curve_ids:        List of curve IDs to query
    :param start_date:       Start of the main date range
    :param end_date:         End of the main date range (inclusive)
    :param nb_days_ahead:    Number of days ahead (typically 1 for day-ahead)
    :param nb_days_forecast: Forecast horizon (days after the 'issue date')
    :param data_name:        Name of the data folder inside the Data directory
    :param data_path:        Path to save date in
    
    :return: Dictionary where each key is a curve id and value is the DataFrame
    """
    # Get raw forecast data, using cache where available
    raw_forecasts, _ = retrieve_forecasts_incremental(
        curve_ids, 
        start_date, 
        end_date, 
        nb_days_ahead, 
        nb_days_forecast,
        data_name=data_name,
        data_path=data_path
    )

    # Parse the forecasts into DataFrames
    dfs = parse_forecasts_by_curve(raw_forecasts, curve_ids)
    today = datetime.now().date()

    # Save each DataFrame to a separate parquet file
    data_dir = os.path.join(data_path, data_name)
    for curve_id, df in dfs.items():
        df_path = os.path.join(data_dir, f"{data_name}_{nb_days_forecast}_days_forecast_curve_{curve_id}_updated_{today}.parquet")
        df.to_parquet(df_path, index=False)
        print(f"✓ Saved parsed data for curve {curve_id} to {df_path}")

    return dfs


def parse_forecasts_by_curve(curves: list, id_list: list[int]) -> dict:
    """
    Parses a list of forecast runs into a dictionary of DataFrames,
    one for each curve id specified in id_list.

    Each forecast run is assumed to be a list of forecast dictionaries,
    where each dictionary has keys such as 'issue_date', 'points', 'id', etc.

    :params curves:  A list of forecast runs (each a list of forecast dictionaries)
    :params id_list: A list of curve ids for which to extract the forecasts
    :return dict:    A dictionary where each key is a curve id from id_list
                     and each value is the corresponding DataFrame.
    """    
    rows = []
    for forecast_run in curves:
        for fr_dict in forecast_run:
            # Extract metadata; ensure forecast_id is of a standard type (e.g., int)
            forecast_id = fr_dict.get("id")
            issue_date  = fr_dict.get("issue_date")
            freq        = fr_dict.get("frequency", None)
            tz          = fr_dict.get("time_zone", None)
            name        = fr_dict.get("name", None)
            created     = fr_dict.get("created", None)
            modified    = fr_dict.get("modified", None)

            # "points" should be a list of [timestamp_millis, predicted_value] pairs
            for (ts_millis, predicted_value) in fr_dict.get("points", []):
                # Convert the millisecond timestamp to a timezone-aware Timestamp
                converted_ts = pd.to_datetime(ts_millis, unit="ms", utc=True)
                converted_ts = converted_ts.tz_convert("Europe/Zurich")
                rows.append({
                    "issue_date": issue_date,
                    "timestamp_ms": converted_ts,
                    "predicted_value": predicted_value,
                    "frequency": freq,
                    "time_zone": tz,
                    "forecast_id": forecast_id,
                    "name": name,
                    "created": created,
                    "modified": modified
                })

    # Build one DataFrame with all forecast points
    df_all = pd.DataFrame(rows)

    if df_all.empty:
        print("WARNING: df_all is empty! Returning empty DataFrames.")
        return {curve_id: pd.DataFrame() for curve_id in id_list}
        
    if 'forecast_id' not in df_all.columns:
        print(f"ERROR: 'forecast_id' column missing! Available columns: {list(df_all.columns)}")
        return {curve_id: pd.DataFrame() for curve_id in id_list}

    # Save df_all to debug folder
    try:
        output_dir = os.path.join("debug")
        os.makedirs(output_dir, exist_ok=True)

        
        # Save as parquet
        parquet_filename = f"df_all_debug_{curve_id}.parquet"
        parquet_path = os.path.join(output_dir, parquet_filename)
        df_all.to_parquet(parquet_path, index=False)
        
        # Save as JSON
        json_filename = f"df_all_debug_{curve_id}.json"
        json_path = os.path.join(output_dir, json_filename)
        df_all.to_json(json_path, orient='records', indent=2, date_format='iso')

        print("✓ Saved debug DataFrame to", parquet_path)
        
    except Exception:
        pass  # Silently ignore any saving errors to not affect functionality

    # Create a dictionary where keys are the curve ids from id_list
    dfs = {}
    for curve_id in id_list:
        df_curve = df_all[df_all["forecast_id"] == curve_id].reset_index(drop=True)
        dfs[curve_id] = df_curve

    return dfs

def parse_forecasts_by_curve_without_parquet(curves: list, id_list: list[int]) -> dict:
    """
    Parses a list of forecast runs into a dictionary of DataFrames,
    one for each curve id specified in id_list.

    Each forecast run is assumed to be a list of forecast dictionaries,
    where each dictionary has keys such as 'issue_date', 'points', 'id', etc.

    :params curves:  A list of forecast runs (each a list of forecast dictionaries)
    :params id_list: A list of curve ids for which to extract the forecasts
    :return dict:    A dictionary where each key is a curve id from id_list
                     and each value is the corresponding DataFrame.
    """    
    rows = []
    for forecast_run in curves:
        for fr_dict in forecast_run:
            # Extract metadata; ensure forecast_id is of a standard type (e.g., int)
            forecast_id = fr_dict.get("id")
            issue_date  = fr_dict.get("issue_date")
            freq        = fr_dict.get("frequency", None)
            tz          = fr_dict.get("time_zone", None)
            name        = fr_dict.get("name", None)
            created     = fr_dict.get("created", None)
            modified    = fr_dict.get("modified", None)

            # "points" should be a list of [timestamp_millis, predicted_value] pairs
            for (ts_millis, predicted_value) in fr_dict.get("points", []):
                # Convert the millisecond timestamp to a timezone-aware Timestamp
                converted_ts = pd.to_datetime(ts_millis, unit="ms", utc=True)
                converted_ts = converted_ts.tz_convert("Europe/Zurich")
                rows.append({
                    "issue_date": issue_date,
                    "timestamp_ms": converted_ts,
                    "predicted_value": predicted_value,
                    "frequency": freq,
                    "time_zone": tz,
                    "forecast_id": forecast_id,
                    "name": name,
                    "created": created,
                    "modified": modified
                })

    # Build one DataFrame with all forecast points
    df_all = pd.DataFrame(rows)

    if df_all.empty:
        print("WARNING: df_all is empty! Returning empty DataFrames.")
        return {curve_id: pd.DataFrame() for curve_id in id_list}
        
    if 'forecast_id' not in df_all.columns:
        print(f"ERROR: 'forecast_id' column missing! Available columns: {list(df_all.columns)}")
        return {curve_id: pd.DataFrame() for curve_id in id_list}

    # Create a dictionary where keys are the curve ids from id_list
    dfs = {}
    for curve_id in id_list:
        df_curve = df_all[df_all["forecast_id"] == curve_id].reset_index(drop=True)
        dfs[curve_id] = df_curve

    return dfs


def get_latest_file(pattern):
    # Get all files matching the pattern
    files = glob.glob(str(pattern))

    # If no files found, return None
    if not files:
        return None
    # Sort files by modification time (newest last)
    latest_file = max(files, key=os.path.getmtime)

    print(f"Using latest file: {latest_file}")
    return latest_file

def merge_forecast_with_latest_day(
    data_path: Path,
    data_name: str,
    pattern: str,
    curve_ids: int,
    nb_days_forecast: int,
    duplicate_cols: list[str],
    latest_data: dict = None,
    debug: bool = False
    ) -> pd.DataFrame:
    """
    Merges the last day of forecast data with the latest available data,
    ensuring that duplicates are handled correctly.
    """
    # load the latest data in a dataframe
    latest_data = latest_data[curve_ids]
    # Create glob pattern and fallback filename separately
    glob_path = data_path / data_name / pattern
    fallback_filename = pattern.rstrip('*') + ".parquet"  # Remove * and add .parquet
    fallback_path = data_path / data_name / fallback_filename
    # Try to load the data directly, otherwise use fallback
    try:
        data = pd.read_parquet(get_latest_file(glob_path) or fallback_path)
        print("Reading the data from", glob_path)
    except Exception as e:
        print(f"Failed to load data directly: {e}")
        print("Falling back to load_and_merge_forecast_data")

        # Infer parameters for load_and_merge_forecast_data
        # Assuming pattern contains information about the data type
        data_name = pattern.split("/")[-1].split("_")[0]  # Extract data name from pattern

        # Use a reasonable date range - adjust as needed
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = datetime(2023, 1, 1).date()

        # Call load_and_merge_forecast_data
        forecast_data = load_and_merge_forecast_data(
            [curve_ids],  # Wrap in list as the function expects a list
            start_date,
            end_date,
            nb_days_ahead=1,
            nb_days_forecast=nb_days_forecast,
            data_name=data_name,
            data_path=data_path
        )

        # Extract the DataFrame for the specific curve_id
        data = forecast_data[curve_ids]

    # Concatenate the last day of forecast data with the latest data
    df_combined = pd.concat([data, latest_data], ignore_index=True)

    # Remove duplicates, keeping the most recent data
    df_combined = df_combined.drop_duplicates(subset=duplicate_cols, keep='last')

    print(f"Shape of {pattern} dataframe:", df_combined.shape)

    # save in the debug folder
    if debug == True:
        try:
            output_dir = os.path.join("debug")
            os.makedirs(output_dir, exist_ok=True)

            # Clean pattern for filename (remove invalid characters)
            clean_pattern = pattern.replace("*", "").replace("/", "_").replace("\\", "_")
            # Save as parquet
            parquet_filename = f"df_combined_debug_{clean_pattern}.parquet"
            parquet_path = os.path.join(output_dir, parquet_filename)
            df_combined.to_parquet(parquet_path, index=False)
            
            # Save as JSON
            json_filename = f"df_combined_debug_{clean_pattern}.json"
            json_path = os.path.join(output_dir, json_filename)
            df_combined.to_json(json_path, orient='records', indent=2, date_format='iso')

            print("✓ Saved debug DataFrame to", parquet_path)
            
        except Exception:
            pass  # Silently ignore any saving errors to not affect functionality


    return df_combined

def retrieve_forecasts_no_cache(
    curve_ids: list[int],
    start_date: date,
    end_date: date,
    nb_days_ahead: int,
    nb_days_forecast: int,
    data_name: str,
    data_path: Path
) -> list:
    """
    Retrieves forecast curves from Volue for each day between start_date and end_date (inclusive),
    using the function get_curves() without any caching mechanism.
    Always fetches fresh data from the API.
    
    :param curve_ids:        List of curve IDs to query (e.g. [24959])
    :param start_date:       Start of the main date range
    :param end_date:         End of the main date range (inclusive)
    :param nb_days_ahead:    Number of days ahead (typically 1 for day-ahead)
    :param nb_days_forecast: Forecast horizon (days after the 'issue date')
    :param data_name:        Name of the data folder inside the Data directory (for saving only)
    :param data_path:        Folder to save data in (for saving only)
    
    :return: A list of raw curve objects (one entry per successful day)
    """
    # Ensure the data directory exists (for saving only)
    data_dir = data_path / data_name
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate the daily date range
    date_list = [
        start_date + timedelta(days=x)
        for x in range((end_date - start_date).days + 1)
    ]

    curves = []
    
    for date_issued in date_list:
        # Calculate forecast date range
        from_date = date_issued + timedelta(days=nb_days_ahead)
        to_date = date_issued + timedelta(days=nb_days_forecast)
        
        try:
            print(f"⏳ Fetching data for issue_date={date_issued}")
            curves_data = get_curves(curve_ids, from_date, to_date, date_issued)
            
            # Optionally save to file with timestamp to ensure unique filenames
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"forecast_{'-'.join(map(str, curve_ids))}_{date_issued.strftime('%Y%m%d')}_{current_time}.json"
            file_path = data_dir / file_name
            
            # Save data to JSON file
            with open(file_path, 'w') as f:
                json.dump(curves_data, f)
            
            curves.append(curves_data)
            
        except HTTPError as ex:
            if ex.response.status_code == 404:
                # Means no forecast for that date/horizon
                print(f"⚠️ No forecast found for issue_date={date_issued}, skipping.")
                continue
            else:
                # Other HTTP errors should be re-raised
                raise
    
    return curves

def load_last_day_forecast_data_no_cache(
    curve_ids: list[int],
    end_date: date,
    nb_days_ahead: int,
    nb_days_forecast: int,
    data_name: str,
    data_path: Path,
    ) -> dict:
    """
    Loads forecast data only for the last day, always fetching fresh data from the API.
    
    :param curve_ids:        List of curve IDs to query
    :param end_date:         The date for which to get forecast data
    :param nb_days_ahead:    Number of days ahead (typically 1 for day-ahead)
    :param nb_days_forecast: Forecast horizon (days after the 'issue date')
    :param data_name:        Name of the data folder inside the Data directory
    :param data_path:        Path to save data in
    
    :return: Dictionary where each key is a curve id and value is the DataFrame
    """
    # We're only getting data for one day (end_date), so start_date = end_date
    start_date = end_date
    
    # Get raw forecast data, always fresh from API
    raw_forecasts = retrieve_forecasts_no_cache(
        curve_ids, 
        start_date, 
        end_date, 
        nb_days_ahead, 
        nb_days_forecast,
        data_name=data_name,
        data_path=data_path
    )
    
    # Parse the forecasts into DataFrames
    dfs = parse_forecasts_by_curve(raw_forecasts, curve_ids)
    today = datetime.now().date()
    current_time = datetime.now().strftime('%H%M%S')
    
    # Save each DataFrame to a separate parquet file with timestamp
    data_dir = data_path / data_name
    for curve_id, df in dfs.items():
        df_path = data_dir / f"{data_name}_{nb_days_forecast}_days_forecast_curve_{curve_id}_updated_{today}_{current_time}.parquet"
        df.to_parquet(df_path, index=False)
        print(f"✓ Saved parsed data for curve {curve_id} to {df_path}")

    return dfs





def get_volue_curve_data_direct(
    curve_ids: list[int],
    date_from: datetime,
    date_to: datetime,
    use_latest: bool = True,
    parse_forecasts_by_curve: bool = True
) -> pd.DataFrame:
    """
    Directly fetch Volue curve data without local caching, similar to read_timeseries_chunked pattern
    
    :param curve_ids: List of curve IDs to query
    :param date_from: Start datetime for the forecast period
    :param date_to: End datetime for the forecast period  
    :param use_latest: If True, use get_latest_curves; if False, use get_curves with today as issue_date
    :return: DataFrame with the curve data
    """
    try:
        print(f"⏳ Reading Volue curves {curve_ids} from {date_from} to {date_to}")
        
        if use_latest:
            # Get the latest available forecasts for the date range
            raw_curves = get_latest_curves(curve_ids, date_from, date_to)
        else:
            # Get forecasts issued today for the date range
            issue_date = datetime.now()
            raw_curves = get_curves(curve_ids, date_from, date_to, issue_date)
        
        # Parse the curves into DataFrames - need to wrap in list for parse function
        if parse_forecasts_by_curve:
            parsed_curves = parse_forecasts_by_curve([raw_curves], curve_ids)
        else:
            parsed_curves = parse_forecasts_by_curve_without_parquet([raw_curves], curve_ids)
        # Return the DataFrame for the first curve ID (assuming single curve like your pattern)
        if curve_ids[0] in parsed_curves:
            df = parsed_curves[curve_ids[0]]
            print(f"✓ Successfully fetched {len(df)} records for curve {curve_ids[0]}")
            
            # Rename columns to match your standard pattern if needed
            if 'timestamp_ms' in df.columns:
                df = df.rename(columns={'timestamp_ms': 'date', 'predicted_value': 'value'})
            
            return df
        else:
            print(f"⚠️ No data found for curve {curve_ids[0]}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"⚠️ Error while reading Volue curve data: {e}")
        return pd.DataFrame()

def get_tagged_curve_tags(curve_id: int) -> list:
    """
    Get all available tags for a tagged instance curve
    
    :param curve_id: The tagged instance curve ID
    :return: List of available tags
    """
    vapi = VolueApi()
    url = f'instances/tagged/{curve_id}/tags'
    return vapi.send_request(url)

def get_latest_tagged_curves(
    curve_ids: List[int], 
    date_from: datetime, 
    date_to: datetime,
    tags: Optional[List[str]] = None
) -> list:
    """
    Get latest tagged instance data for a time range
    
    :param curve_ids: List of tagged instance curve IDs to get data from
    :param date_from: Start datetime for data (inclusive)
    :param date_to: End datetime for data (exclusive)  
    :param tags: Optional list of tags to filter by
    :return: List of requested curve objects
    """
    # Build request
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str = date_to.strftime("%Y-%m-%d")

    data = []
    for curve_id in curve_ids:
        # Build URL with parameters
        url = f'instances/tagged/{curve_id}/latest?data_from={date_from_str}&data_to={date_to_str}'
        
        # Add tags if specified
        if tags:
            for tag in tags:
                url += f'&tag={tag}'
        
        # Query and get results
        vapi = VolueApi()
        data.append(vapi.send_request(url))
    return data

def get_tagged_curves(
    curve_ids: List[int], 
    date_from: datetime, 
    date_to: datetime, 
    issue_date: datetime,
    tags: Optional[List[str]] = None
) -> list:
    """
    Get tagged instance data for a specific issue date and time range
    
    :param curve_ids: List of tagged instance curve IDs
    :param date_from: Start datetime for forecast period (inclusive)
    :param date_to: End datetime for forecast period (exclusive)
    :param issue_date: Date when the forecast was issued
    :param tags: Optional list of tags to filter by
    :return: List of requested curve objects
    """
    # Build request
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str = date_to.strftime("%Y-%m-%d")
    issue_date_str = issue_date.strftime("%Y-%m-%d")

    data = []
    for curve_id in curve_ids:
        # Build URL
        url = (
            f"instances/tagged/{curve_id}/get"
            f"?issue_date={issue_date_str}"
            f"&from={date_from_str}"
            f"&to={date_to_str}"
        )
        
        # Add tags if specified
        if tags:
            for tag in tags:
                url += f'&tag={tag}'
        
        # Query and get results
        vapi = VolueApi()
        data.append(vapi.send_request(url))
    return data

def _build_ingest_payload_from_tagged_raw(raw_curves: list, *, default_tz: str = "Europe/Zurich") -> list[dict]:
    """Convert the Volue tagged raw response into an ingest_points_json-compatible payload.

    Output format (list of items):
    [
      {
        "name": <str>,                 # used by ingest.ensure_series() if series_id is unknown
        "time_zone": <str>,           # e.g. "Europe/Zurich"; used for timestamp parsing when no tz on points
        "modified": <str>,            # ISO string used as issue_time when use_modified_as_issue_time=True
        "tag": <str|None>,            # carried over for downstream visibility
        "points": [[ts_ms, value], ...]  # pairs; ingest auto-detects ms vs s epoch
      },
      ...
    ]
    NOTE: We *do not* include a top-level "id" field to avoid it being interpreted
    by ingest as an internal series_id (Volue IDs aren't DB series IDs).
    """
    items: list[dict] = []

    def _push(instance: dict):
        # Minimal, safe metadata for ingest.ensure_series(); we prefer provider/type/etc. to be handled upstream
        name = instance.get("name") or "volue_tagged_curve"
        tz = instance.get("time_zone") or default_tz
        modified = instance.get("modified")  # string or ISO; ingest knows how to parse
        tag = instance.get("tag")
        points = instance.get("points", [])
        if not isinstance(points, list):
            points = []
        # Keep points as list[list] with [epoch_ms, value]; ingest handles ms/seconds
        items.append({
            "name": name if not tag else f"{name} [{tag}]",
            "time_zone": tz,
            "modified": modified,
            "tag": tag,
            "points": points,
        })

    for curve_data in raw_curves:
        if isinstance(curve_data, dict):
            _push(curve_data)
        elif isinstance(curve_data, list):
            for instance in curve_data:
                if isinstance(instance, dict):
                    _push(instance)
        elif isinstance(curve_data, str):
            try:
                import json as _json
                parsed = _json.loads(curve_data)
                if isinstance(parsed, dict):
                    _push(parsed)
                elif isinstance(parsed, list):
                    for instance in parsed:
                        if isinstance(instance, dict):
                            _push(instance)
            except Exception:
                continue
        else:
            continue

    return items


def get_tagged_curve_data_direct(
    curve_ids: list[int],
    date_from: datetime,
    date_to: datetime,
    use_latest: bool = True,
    tags: Optional[List[str]] = None,
    issue_date: Optional[datetime] = None,
    *,
    output: Literal["json", "dataframe"] = "json",
) -> "pd.DataFrame | list[dict]":
    """
    Directly fetch tagged instance curve data.

    When `output="json"` (default), this returns a payload **ready** for `ingest_points_json(...)`.
    When `output="dataframe"`, the previous DataFrame behavior is preserved.
    """
    try:
        print(f"⏳ Reading Volue tagged curves {curve_ids} from {date_from} to {date_to}")

        # If no tags specified, try to get available tags for the first curve (best-effort)
        if tags is None:
            try:
                available_tags = get_tagged_curve_tags(curve_ids[0])
                tags = available_tags[:1] if available_tags else None  # use the first tag if any
                if tags:
                    print(f"🏷️ Using tag: {tags[0]}")
            except Exception as e:
                print(f"⚠️ Could not get tags: {e}")
                tags = None

        if use_latest:
            raw_curves = get_latest_tagged_curves(curve_ids, date_from, date_to, tags)
        else:
            if issue_date is None:
                issue_date = datetime.now()
            raw_curves = get_tagged_curves(curve_ids, date_from, date_to, issue_date, tags)

        if output == "json":
            payload = _build_ingest_payload_from_tagged_raw(raw_curves)
            print(f"✓ Built ingest payload with {sum(len(x.get('points', [])) for x in payload)} points across {len(payload)} item(s)")
            return payload

        # Legacy: DataFrame path
        parsed_curves = parse_tagged_forecasts_by_curve(raw_curves, curve_ids)
        if curve_ids[0] in parsed_curves:
            df = parsed_curves[curve_ids[0]]
            if 'timestamp_ms' in df.columns:
                df = df.rename(columns={'timestamp_ms': 'date', 'predicted_value': 'value'})
            print(f"✓ Successfully fetched {len(df)} records for tagged curve {curve_ids[0]}")
            return df
        else:
            print(f"⚠️ No data found for tagged curve {curve_ids[0]}")
            import pandas as pd
            return pd.DataFrame()

    except Exception as e:
        print(f"⚠️ Error while reading Volue tagged curve data: {e}")
        import traceback
        traceback.print_exc()
        if output == "json":
            return []
        else:
            import pandas as pd
            return pd.DataFrame()
            
    except Exception as e:
        print(f"⚠️ Error while reading Volue tagged curve data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def parse_tagged_forecasts_by_curve(raw_curves: list, curve_ids: list[int]) -> dict:
    """
    Parse tagged instance curve data into DataFrames
    
    :param raw_curves: Raw data from tagged instance curve API
    :param curve_ids: List of curve IDs
    :return: Dictionary with curve_id as key and DataFrame as value
    """
    rows = []
    
    print(f"🔧 Parsing tagged curve data...")
    print(f"Raw curves type: {type(raw_curves)}, length: {len(raw_curves)}")
    
    for i, curve_data in enumerate(raw_curves):
        print(f"Processing curve data {i}: type = {type(curve_data)}")
        
        # Handle different possible structures
        if isinstance(curve_data, dict):
            # Direct dictionary format - single instance
            process_tagged_instance(curve_data, rows)
            
        elif isinstance(curve_data, list):
            # List of instances
            for instance in curve_data:
                if isinstance(instance, dict):
                    process_tagged_instance(instance, rows)
                else:
                    print(f"⚠️ Unexpected instance type: {type(instance)}")
                    
        elif isinstance(curve_data, str):
            print(f"⚠️ Got string data (possible JSON?): {curve_data[:100]}...")
            # Try to parse as JSON
            try:
                import json
                parsed = json.loads(curve_data)
                if isinstance(parsed, dict):
                    process_tagged_instance(parsed, rows)
                elif isinstance(parsed, list):
                    for instance in parsed:
                        if isinstance(instance, dict):
                            process_tagged_instance(instance, rows)
            except json.JSONDecodeError:
                print(f"❌ Could not parse string as JSON")
        else:
            print(f"⚠️ Unexpected curve data type: {type(curve_data)}")
    
    # Build DataFrame
    df_all = pd.DataFrame(rows)
    
    if df_all.empty:
        print("WARNING: df_all is empty! Returning empty DataFrames.")
        return {curve_id: pd.DataFrame() for curve_id in curve_ids}
    
    print(f"✓ Built DataFrame with {len(df_all)} rows")
    print(f"Columns: {list(df_all.columns)}")
    
    # Create dictionary for each curve ID
    dfs = {}
    for curve_id in curve_ids:
        if 'forecast_id' in df_all.columns:
            df_curve = df_all[df_all["forecast_id"] == curve_id].reset_index(drop=True)
        else:
            # If no forecast_id column, assume all data is for the first curve
            df_curve = df_all.copy()
        dfs[curve_id] = df_curve
    
    return dfs

def process_tagged_instance(instance_dict: dict, rows: list):
    """
    Process a single tagged instance dictionary and add rows to the list
    """
    # Extract metadata
    forecast_id = instance_dict.get("id")
    issue_date = instance_dict.get("issue_date")
    freq = instance_dict.get("frequency", None)
    tz = instance_dict.get("time_zone", None)
    name = instance_dict.get("name", None)
    created = instance_dict.get("created", None)
    modified = instance_dict.get("modified", None)
    tag = instance_dict.get("tag", None)  # Tagged curves might have this
    
    # Process points
    points = instance_dict.get("points", [])
    for point in points:
        if isinstance(point, list) and len(point) >= 2:
            ts_millis, predicted_value = point[0], point[1]
            # Convert timestamp
            converted_ts = pd.to_datetime(ts_millis, unit="ms", utc=True)
            converted_ts = converted_ts.tz_convert("Europe/Zurich")
            
            rows.append({
                "issue_date": issue_date,
                "timestamp_ms": converted_ts,
                "predicted_value": predicted_value,
                "frequency": freq,
                "time_zone": tz,
                "forecast_id": forecast_id,
                "name": name,
                "created": created,
                "modified": modified,
                "tag": tag
            })