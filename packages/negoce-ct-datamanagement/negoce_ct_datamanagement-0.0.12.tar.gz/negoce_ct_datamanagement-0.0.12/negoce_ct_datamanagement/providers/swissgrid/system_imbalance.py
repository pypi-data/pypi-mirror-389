import requests
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO


SWISSGRID_IMBALANCE_MAPPING = {
    'Date Time': 'datetime',
    'Abgedeckte Bedarf der aFRR+': 'afrr_pos',
    'Abgedeckte Bedarf der aFRR-': 'afrr_neg',
    'NRV+ (Import)': 'nrv_pos',
    'NRV- (Export)': 'nrv_neg',
    'Abgedeckte Bedarf der SA mFRR+': 'mfrr_sa_pos',
    'Abgedeckte Bedarf der SA mFRR-': 'mfrr_sa_neg',
    'Abgedeckte Bedarf der DA mFRR+': 'mfrr_da_pos',
    'Abgedeckte Bedarf der DA mFRR-': 'mfrr_da_neg',
    'Abgedeckte Bedarf der RR+': 'rr_pos',
    'Abgedeckte Bedarf der RR-': 'rr_neg',
    'FRCE+ (Import)': 'frce_pos',
    'FRCE- (Export)': 'frce_neg',
    'Total System Imbalance (Positiv = long / Negativ = short)': 'total_imbalance',
    'AE-Preis long': 'prices_long',
    'AE-Preis short': 'prices_short',
    'AE-Preis per 2026': 'prices_single'
}


def _format_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format dataframe
    :param df:
    :return: dataframe formatted
    """
    # convert €t/kWh to €/MWh
    try:
        df['prices_long'] = df['prices_long'] * 10
        df['prices_short'] = df['prices_short'] * 10
        df['prices_single'] = df['prices_single'] * 10
    except KeyError:
        # if not present, do nothing
        pass
    
    # round all df; trick to handle datetime column
    df.set_index('datetime', inplace=True)
    df = df.astype(float).round(2)
    df.reset_index(inplace=True)
    
    # parse datetime to be ISO - handle different formats
    df['datetime'] = df['datetime'].apply(lambda x: 
        # Check if input is already a datetime object
        x.replace(tzinfo=ZoneInfo("Europe/Zurich")).isoformat() if isinstance(x, datetime) 
        else (
            # Try format with seconds
            datetime.strptime(x, '%d.%m.%Y %H:%M:%S').replace(tzinfo=ZoneInfo("Europe/Zurich")).isoformat()
            if ':' in x and x.count(':') == 2
            # Try format without seconds
            else datetime.strptime(x, '%d.%m.%Y %H:%M').replace(tzinfo=ZoneInfo("Europe/Zurich")).isoformat()
        )
    )
    
    df['timestamp'] = df['datetime'].apply(lambda x: datetime.fromisoformat(x).timestamp() * 1000)
    # add area
    df['area'] = 'CH'
    return df


def get_rt_system_imbalance(filtered_date: date) -> pd.DataFrame:
    """
    get real time imbalance system data
    :return:
    """
    base_url = "https://www.swissgrid.ch/content/dam/dataimport/control-area-balance/control-area-balance-daily"
    resp = requests.get(base_url + ".xlsx")
    resp_csv = requests.get(base_url + ".csv")
    # take most recent one
    resp_dt = datetime.strptime(resp.headers.get('last-modified'), "%a, %d %b %Y %H:%M:%S GMT")
    resp_csv_dt = datetime.strptime(resp_csv.headers.get('last-modified'), "%a, %d %b %Y %H:%M:%S GMT")
    if resp_dt >= resp_csv_dt:
        df = pd.read_excel(BytesIO(resp.content))
    else:
        df = pd.read_csv(BytesIO(resp_csv.content), sep=';')
    df.rename(columns=SWISSGRID_IMBALANCE_MAPPING, inplace=True)
    df = _format_df(df)
    # keep only today
    df = df[df['datetime'].apply(lambda x: datetime.fromisoformat(x).date() == filtered_date)]
    df.reset_index(drop=True, inplace=True)
    # Fixed code for handling empty dataframe from swissgrid at midnight
    if df.empty:
        # Handle empty DataFrame - no data available
        print(f"Warning: No system imbalance data available for {datetime.today().date()}. Returning empty DataFrame.")
        return pd.DataFrame()  # Return empty DataFrame or appropriate default
    else:
        # Original logic when df has data
        for i in range(0, max(0, 95 - df.index[-1])):
            last_dt = df.iloc[-1]['datetime']
            # add empty row and update datetime / timestamp
            df.loc[len(df)] = pd.Series(dtype='float64')
            df.loc[df.index[-1], 'datetime'] = (datetime.fromisoformat(last_dt) + timedelta(minutes=15)).isoformat()
            df.loc[df.index[-1], 'timestamp'] = datetime.fromisoformat(df.loc[df.index[-1], 'datetime']).timestamp() * 1000
    df['modified'] = datetime.now().astimezone(ZoneInfo("Europe/Zurich")).isoformat()
    return df


def get_ytd_system_imbalance(year: int) -> pd.DataFrame:
    """
    get year-to-date (ytd) imbalance system data
    :param year:
    :return: combined dataframe for the full year
    """
    dfs = []
    
    # Handle special case for 2024
    if year == 2024:
        # First file: January to December 12th (with "-net" suffix)
        filename1 = f'control-area-balance-{year}-net'
        url1 = f'https://www.swissgrid.ch/content/dam/dataimport/control-area-balance/{filename1}.xlsx'
        
        # Second file: November to end of year (standard naming)
        filename2 = f'control-area-balance-{year}'
        url2 = f'https://www.swissgrid.ch/content/dam/dataimport/control-area-balance/{filename2}.xlsx'
        
        # Process first file
        resp1 = requests.get(url1)
        try:
            df1 = pd.read_excel(BytesIO(resp1.content))
            df1.rename(columns=SWISSGRID_IMBALANCE_MAPPING, inplace=True)
            df1 = _format_df(df1)
            dfs.append(df1)
        except Exception as e:
            print(f"Error processing first 2024 file: {e}")
        
        # Process second file
        resp2 = requests.get(url2)
        try:
            df2 = pd.read_excel(BytesIO(resp2.content))
            df2.rename(columns=SWISSGRID_IMBALANCE_MAPPING, inplace=True)
            df2 = _format_df(df2)
            dfs.append(df2)
        except Exception as e:
            print(f"Error processing second 2024 file: {e}")
    
    else:
        # Standard processing for other years
        filename = f'control-area-balance-{year}'
        url = f'https://www.swissgrid.ch/content/dam/dataimport/control-area-balance/{filename}.xlsx'
        resp = requests.get(url)
        try:
            df = pd.read_excel(BytesIO(resp.content))
        except ValueError as e:
            print(f"Error reading Excel file: {e}")
            try:
                # Try reading as CSV if Excel fails
                df = pd.read_csv(BytesIO(resp.content), sep=';')
            except Exception as csv_error:
                print(f"Error reading CSV file: {csv_error}")
                raise ValueError("Failed to read both Excel and CSV formats.") from csv_error
        
        df.rename(columns=SWISSGRID_IMBALANCE_MAPPING, inplace=True)
        df = _format_df(df)
        dfs.append(df)
    
    # If we have multiple dataframes, combine them
    if len(dfs) > 1:
        # Concatenate all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates based on datetime
        combined_df.drop_duplicates(subset=['datetime'], keep='last', inplace=True)
        
        # Sort by datetime
        combined_df.sort_values('datetime', inplace=True)
        combined_df.reset_index(drop=True, inplace=True)
    else:
        combined_df = dfs[0]
    
    combined_df['modified'] = datetime.now().astimezone(ZoneInfo("Europe/Zurich")).isoformat()
    return combined_df
