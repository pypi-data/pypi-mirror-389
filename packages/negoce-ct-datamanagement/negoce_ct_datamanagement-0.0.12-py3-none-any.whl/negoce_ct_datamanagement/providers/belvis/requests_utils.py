import json
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, Tuple, Dict, List
import pandas as pd
import os
from pathlib import Path

from negoce_ct_datamanagement.providers.belvis._config import BelvisApi, BelvisMethod


class ReadOptions(BaseModel):
    blocking: Optional[bool] = False
    precision: Optional[int] = 3
    taskid: Optional[int] = None
    taskname: Optional[str] = None


class WriteOptions(BaseModel):
    blocking: Optional[bool] = True  # if true and > 10s then return error; idf false return error if checked out by another process
    markDependencies: Optional[bool] = True  #  recalculation of dependent time series
    checkOrigin: Optional[bool] = False  # false: Writing is possible at any time
    allowHistoricalData: Optional[bool] = True  # true: Writing is possible in all time ranges
    taskid: Optional[int] = None
    taskname: Optional[str] = None


class ReadPropertiesOptions(BaseModel):
    technical: Optional[bool] = True  # The technical characteristics such as specification, Time series resolution and type of time series are determined
    physical: Optional[bool] = True  # The physical properties such as the unit of values and Freeze marks of the time series are determined
    functional: Optional[bool] = True  # The functional properties such as assignment of the time series to Balancing group and supplier are determined. The assigned instances are displayed with their ident
    Embed: Optional[bool] = True  # In addition to the determined subject assignments, further Information provided (name, short name, market partner code).
    taskid: Optional[int] = None
    taskname: Optional[str] = None


# note: warning belvis strat day at 00:15 and finish it at 00:00 day after
def read_timeseries(timeseries_id: int, date_from: datetime, date_to: datetime, tenant: str ='SGB_SIG', options: ReadOptions = ReadOptions()):
    """

    :param timeseries_id:
    :param date_from:
    :param date_to:
    :param options:
    :return:
    """
    endpoint = f'/timeseries/{timeseries_id}/values?timeRange={date_from.isoformat(timespec="minutes")}--{date_to.isoformat(timespec="minutes")}&timeRangeType=inclusive-exclusive'
    # build endpoint query params
    if options is not None:
        for idx, option in enumerate(options):
            if option[1] is not None:
                prefix = '&'
                endpoint = f'{endpoint}{prefix}{option[0]}={str(option[1]).lower()}'
    belvis_api = BelvisApi(tenant=tenant)
    resp = belvis_api.send_request(
        endpoint=endpoint,
        method=BelvisMethod.get,
    )
    return resp

def format_belvis_data(data: pd.DataFrame, name: str) -> pd.DataFrame:
    # Convert the 'Date' column to datetime
    if isinstance(data, list):
        data = pd.DataFrame(data)
    data.rename(columns={'ts': 'datetime'}, inplace=True)

    # Set the 'Date' column as the index
    data.set_index('datetime', inplace=True)

    # Convert the date format to match the past_data format
    data.index = pd.to_datetime(data.index)  # Parse ISO 8601 format
    data.index = data.index.tz_convert('Europe/Zurich')  # Convert to +02:00 timezone
    
    # rename the values columns
    data.rename(columns={'v': name}, inplace=True)

    # Drop useless columns
    data.drop(columns=['pf'], inplace=True, errors='ignore')

    return data
    
def read_timeseries_cached(
timeseries_id: int, 
date_from: datetime, 
date_to: datetime,
data_name: str,
cache_dir: Path,
options: ReadOptions = ReadOptions(),
chunk_size_days: int = 1,
previously_fetched_data: dict = None,
tenant: str = 'SGB_SIG'
) -> Tuple[pd.DataFrame, Dict]:
    """
    Reads timeseries data with caching capability to avoid reloading all data.
    Data is split into daily chunks and cached in JSON files, like the original implementation.
    Only missing data chunks are fetched from the API.
    
    :param timeseries_id:        ID of the timeseries to read
    :param date_from:            Start date (inclusive)
    :param date_to:              End date (exclusive)
    :param options:              ReadOptions for the API call (Pydantic BaseModel)
    :param cache_dir:            Directory to store cached data
    :param chunk_size_days:      Size of each chunk in days (default: 1 day chunks)
    :param previously_fetched_data: Dictionary with previously fetched data
    :param data_name:            Name of the data folder inside the cache directory
    
    :return: Tuple containing:
            1. DataFrame with the complete requested timeseries data
            2. Updated cache dictionary
    """
    # Set the default value for cache_dir if not provided
    if cache_dir is None:
        cache_dir = os.path.join("data", f"{data_name}_cache")            
    # Ensure the data directory exists
    cache_index_path = cache_dir / "cache_index.parquet"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Load cache index or create a new one
    cache = {}
    if previously_fetched_data is None:
        if cache_index_path.exists():
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
    
    # Generate chunks covering the requested date range        
    # Create list of date chunks
    chunks = []
    current_date = date_from
    while current_date < date_to:
        chunk_end = min(current_date + timedelta(days=chunk_size_days), date_to)
        chunks.append((current_date, chunk_end))
        current_date = chunk_end
    
    # Initialize storage for the data
    all_data = []
    new_cache_entries = []
    new_data_fetched = False
    
    # Convert Pydantic model to a string representation for cache key
    options_dict = options.model_dump(exclude_none=True)  # Get non-None values as dict
    options_str = "_".join([f"{k}={v}" for k, v in options_dict.items()])
    
    # Process each chunk
    for chunk_start, chunk_end in chunks:
        # Create a cache key for this specific request
        cache_key = f"{timeseries_id}_{chunk_start.strftime('%Y-%m-%d_%H-%M')}_{chunk_end.strftime('%Y-%m-%d_%H-%M')}_{options_str}"
        
        # Check if we already have this data in cache
        if cache_key in cache:
            file_path = cache[cache_key]
            if os.path.exists(file_path):
                print(f"✓ Using cached data for timeseries={data_name}, period={chunk_start} to {chunk_end}")
                try:
                    with open(file_path, 'r') as f:
                        chunk_data = json.load(f)
                    all_data.append(chunk_data)
                    continue
                except Exception as e:
                    print(f"⚠️ Error reading cached file {file_path}: {e}")
                    # If error, we'll fetch it again
        
        # If not in cache or error reading file, fetch from API
        try:
            print(f"⏳ Fetching new data for timeseries={data_name}, period={chunk_start} to {chunk_end}")
            # Call the original read_timeseries function
            response_data = read_timeseries(timeseries_id, chunk_start, chunk_end, tenant, options)
            new_data_fetched = True
            
            # Generate unique filename for this chunk
            file_name = f"{data_name}_{timeseries_id}_{chunk_start.strftime('%Y%m%d_%H%M')}_{chunk_end.strftime('%Y%m%d_%H%M')}.json"
            cache_subdirectory = os.path.join(cache_dir, data_name)
            os.makedirs(cache_subdirectory, exist_ok=True)  # Create subdirectory if it doesn't exist
            file_path = os.path.join(cache_subdirectory, file_name)
            
            # Save raw data to JSON file (just like in your original implementation)
            with open(file_path, 'w') as f:
                json.dump(response_data, f)
            
            # Update cache entry
            cache[cache_key] = file_path
            new_cache_entries.append({
                'cache_key': cache_key,
                'file_path': file_path,
                'timeseries_id': timeseries_id,
                'chunk_start': chunk_start.strftime('%Y-%m-%d %H:%M'),
                'chunk_end': chunk_end.strftime('%Y-%m-%d %H:%M'),
                'options': options_str
            })
            
            all_data.append(response_data)
            
        except Exception as e:
            print(f"⚠️ Error fetching data for time range {chunk_start} to {chunk_end}: {e}")
            # Continue with other chunks even if one fails
    
    # Save updated cache index if new data was fetched
    if new_data_fetched and new_cache_entries:
        try:
            # Create or update the cache index DataFrame
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
    
    # Now format all the data into a DataFrame
    if all_data:
        # We'll process all the raw data after loading it from cache/API
        combined_df = format_all_data(all_data, timeseries_id, data_name)
        
        # Save the final combined DataFrame as parquet
        today = datetime.now().date()
        combined_path = os.path.join(cache_dir, f"{data_name}_timeseries_{timeseries_id}_updated_{today}.parquet")
        combined_df.to_parquet(combined_path)
        print(f"✓ Saved combined data for timeseries {timeseries_id} to {combined_path}")
        
        return combined_df, cache
    else:
        # Return empty DataFrame if no data was found
        return pd.DataFrame(), cache

def read_timeseries_chunked(
    timeseries_id: int,
    date_from: datetime,
    date_to: datetime,
    options: ReadOptions = ReadOptions(),
    chunk_size_days: int = 7,
    tenant: str = 'SGB_SIG'
) -> List[Dict]:
    """
    Efficiently reads a time series over long date ranges WITHOUT using local cache.
    Splits the period into smaller chunks to avoid large, slow, or error-prone API requests.

    :param timeseries_id:     The time series ID to fetch
    :param date_from:         Start datetime (inclusive)
    :param date_to:           End datetime (exclusive)
    :param options:           Read options (precision, blocking, etc.)
    :param chunk_size_days:   Number of days per request chunk (default: 7)
    :return: A list of dictionaries (as returned by `read_timeseries`) containing time series data
    """
    current = date_from
    results = []

    while current < date_to:
        chunk_end = min(current + timedelta(days=chunk_size_days), date_to)
        try:
            print(f"⏳ Reading Belvis timeseries {timeseries_id} from {current} to {chunk_end}")
            chunk = read_timeseries(timeseries_id, current, chunk_end, tenant, options)
            results.extend(chunk)
        except Exception as e:
            print(f"⚠️ Error while reading data from {current} to {chunk_end}: {e}")
        current = chunk_end

    return results

def format_all_data(raw_data_chunks, timeseries_id, name: str) -> pd.DataFrame:
    """
    Format all the raw data chunks into a single DataFrame.
    
    :param raw_data_chunks: List of raw data responses from the API or cache
    :param timeseries_id: The timeseries ID (for logging)
    :return: A combined and formatted DataFrame
    """
    # Initialize list to hold DataFrames
    dfs = []
    
    # Process each chunk
    for chunk in raw_data_chunks:
        try:
            chunk_df = format_belvis_data(chunk, name)
            dfs.append(chunk_df)
        except Exception as e:
            print(f"⚠️ Error formatting chunk for timeseries {name}: {e}")
    
    # Combine all DataFrames
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=False)  # Keep original indices
        # If timestamp is in the index (not a column)
        if isinstance(combined_df.index, pd.DatetimeIndex):
            # Drop duplicates based on index
            combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
            # Sort by index
            combined_df = combined_df.sort_index()
        # If timestamp is a column
        elif 'timestamp' in combined_df.columns:
            combined_df = combined_df.drop_duplicates(subset='timestamp', keep='first')
            combined_df = combined_df.sort_values('timestamp')
        
        return combined_df
    else:
        return pd.DataFrame()

# note: warning belvis strat day at 00:15 and finish it at 00:00 day after
def write_timeseries(timeseries_id: int, data: list, tenant: str ='SGB_SIG', options: WriteOptions = WriteOptions()):
    """

    :param timeseries_id:
    :param data:
    :param options:
    :return:
    """
    endpoint = f'/timeseries/{timeseries_id}/values'
    # build endpoint query params
    if options is not None:
        for idx, option in enumerate(options):
            if option[1] is not None:
                prefix = '&'
                if idx == 0:
                    prefix = '?'
                endpoint = f'{endpoint}{prefix}{option[0]}={str(option[1]).lower()}'
    belvis_api = BelvisApi(tenant=tenant)
    resp = belvis_api.send_request(
        endpoint=endpoint,
        method=BelvisMethod.put,
        data=json.dumps(data)
    )
    return resp


def read_timeseries_properties(timeseries_id: int, tenant: str ='SGB_SIG', options: ReadPropertiesOptions = ReadPropertiesOptions()):
    """

    :param timeseries_id:
    :param options:
    :return:
    """
    endpoint = f'/timeseries/{timeseries_id}/properties'
    # build endpoint query params
    if options is not None:
        for idx, option in enumerate(options):
            if option[1] is not None:
                prefix = '&' if idx != 0 else '?'
                endpoint = f'{endpoint}{prefix}{option[0]}={str(option[1]).lower()}'
    belvis_api = BelvisApi(tenant=tenant)
    resp = belvis_api.send_request(
        endpoint=endpoint,
        method=BelvisMethod.get,
    )
    return resp


def read_timeseries_statistics(timeseries_id: int, date_from: datetime, date_to: datetime,  tenant: str ='SGB_SIG', options: ReadOptions = ReadOptions()):
    """

    :param timeseries_id:
    :param date_from:
    :param date_to:
    :param options:
    :return:
    """
    endpoint = f'/timeseries/{timeseries_id}/statistics?timeRange={date_from.isoformat(timespec="minutes")}--{date_to.isoformat(timespec="minutes")}&timeRangeType=inclusive-exclusive'
    # build endpoint query params
    if options is not None:
        for idx, option in enumerate(options):
            if option[1] is not None:
                prefix = '&'
                endpoint = f'{endpoint}{prefix}{option[0]}={str(option[1]).lower()}'
    belvis_api = BelvisApi(tenant=tenant)
    resp = belvis_api.send_request(
        endpoint=endpoint,
        method=BelvisMethod.get,
    )
    return resp


def load_and_merge_all_data(
    timeseries_id: int,
    data_name: str,
    cache_dir: Path,
    recent_df: pd.DataFrame,
    start_year: int = 2010,
    end_year: int = 2024
) -> pd.DataFrame:
    """
    Load all consolidated yearly files and merge with recent data.
    
    :param timeseries_id: The timeseries ID
    :param data_name: Name of the data (e.g., "temperature")
    :param cache_dir: Root cache directory
    :param recent_df: DataFrame with recent data (from read_timeseries_cached)
    :param start_year: First year to load
    :param end_year: Last year to load
    :return: Complete DataFrame with all historical and recent data
    """
    cache_dir = Path(cache_dir)
    consolidated_dir = cache_dir / data_name / "consolidated"
    
    all_dfs = []
    
    # Load consolidated yearly files
    for year in range(start_year, end_year + 1):
        consolidated_file = consolidated_dir / f"{data_name}_{timeseries_id}_{year}_consolidated.json"
        
        if consolidated_file.exists():
            try:
                with open(consolidated_file, 'r') as f:
                    year_data = json.load(f)
                
                # Convert to DataFrame
                if isinstance(year_data, list) and len(year_data) > 0:
                    # Convert list of dicts to DataFrame
                    year_df = pd.DataFrame(year_data)
                    
                    # Convert timestamp string to datetime
                    year_df['ts'] = pd.to_datetime(year_df['ts'])
                    
                    # Rename columns to match the format from read_timeseries_cached
                    # Assuming recent_df has columns like 'timestamp', 'value', etc.
                    year_df = year_df.rename(columns={
                        'ts': 'timestamp',
                        'v': 'value'
                    })
                    
                    # Add timeseries_id and data_name columns
                    year_df['timeseries_id'] = timeseries_id
                    year_df['data_name'] = data_name
                    
                    all_dfs.append(year_df)
                    print(f"✓ Loaded {len(year_df)} records from year {year}")
                
            except Exception as e:
                print(f"Error loading year {year}: {e}")
    
    # Add recent data
    if not recent_df.empty:
        # Check if columns match, if not try to standardize
        if 'ts' in recent_df.columns and 'timestamp' not in recent_df.columns:
            recent_df = recent_df.rename(columns={'ts': 'timestamp', 'v': 'value'})
        all_dfs.append(recent_df)
        print(f"✓ Added {len(recent_df)} recent records")
    
    # Combine all dataframes
    if all_dfs:
        complete_df = pd.concat(all_dfs, ignore_index=True)
        
        # Remove duplicates if any (keep last occurrence)
        if 'timestamp' in complete_df.columns:
            complete_df = complete_df.sort_values('timestamp')
            complete_df = complete_df.drop_duplicates(subset=['timestamp'], keep='last')
        
        print(f"\n📊 Total records: {len(complete_df)}")
        return complete_df
    else:
        print("No data found")
        return pd.DataFrame()


if __name__ == '__main__':
    from zoneinfo import ZoneInfo
    from dotenv import load_dotenv
    import sys
    # load .env.development file
    ENV = "development"
    ENV_PATH = str(Path(__file__).parents[3] / f'.env.{ENV}')
    is_loaded = load_dotenv(ENV_PATH)
    if not is_loaded:
        print(f"ERROR: env file not loaded: {ENV_PATH}")

    # params
    # shift +15mn for BelVis convention (if timeseries has granularity of 15 minutes)

    # # belvis health check
    # BelvisApi = BelvisApi()
    # ping = BelvisApi.ping()
    # sysinfo = BelvisApi.sysinfo()
    # monitor = BelvisApi.monitor()
    # a = 1

    data = read_timeseries(
        timeseries_id=53232640,
        date_from=datetime(2025, 7, 30).astimezone(ZoneInfo("Europe/Zurich")) + timedelta(minutes=15),
        date_to=datetime(2025, 7, 31).astimezone(ZoneInfo("Europe/Zurich")) + timedelta(minutes=15),
    )
    data_properties = read_timeseries_properties(
        timeseries_id=53232640
    )
    data_stats = read_timeseries_statistics(
        timeseries_id=53232640,
        date_from=datetime(2025, 7, 30).astimezone(ZoneInfo("Europe/Zurich")) + timedelta(minutes=15),
        date_to=datetime(2025, 7, 31).astimezone(ZoneInfo("Europe/Zurich")) + timedelta(minutes=15),
    )
    a = 1