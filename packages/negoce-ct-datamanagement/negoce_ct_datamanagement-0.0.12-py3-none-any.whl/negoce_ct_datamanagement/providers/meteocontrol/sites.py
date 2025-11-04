from typing import List
import pandas as pd
import asyncio

from negoce_ct_datamanagement.providers.meteocontrol._config import (
    get_api,
    get_api_async,
)
semaphore = asyncio.Semaphore(30)
def get_systems() -> List[dict]:
    """
    Returns an array of system objects
    Example of one item in list: {'key': 'C19WC', 'name': 'SPI8.10_Lignon_Bât_24_25_26'}
    """
    api = get_api()
    resp = api.send_request(endpoint="systems")
    return resp['data']

def get_system_object(system_key: str, with_technical_dat: bool = True):
    """
    Return detailed system data
    """
    api = get_api()
    resp = api.send_request(endpoint=f"systems/{system_key}")
    return resp['data']

def get_all_system_objects(with_technical_dat: bool = True) -> pd.DataFrame:
    """
    Return all systems objects with optional technical data
    """
    raw = []
    systems = get_systems()
    for system in systems:
        obj = get_system_object(system['key'])
        raw.append(obj)
    # process data to return clean dataframe
    df = pd.DataFrame(raw)
    return df

async def get_nominal_power(system_key: str) -> float:
    """
    Retrieve the nominal power (in kWp) for a specific system.
    """
    api = get_api_async()
    try:
        async with semaphore:
            response = await api.send_request(f"systems/{system_key}/technical-data")
            return response.get("data", {}).get("nominalPower", 0.0)
    except Exception as e:
        print(f"[{system_key}] Failed to get nominal power: {e}")
        return 0.0


if __name__ == '__main__':
    # define env here
    import os
    os.chdir(os.path.dirname(__file__))
    from zoneinfo import ZoneInfo
    os.environ["ENV"] = "development"
    # load env variables from .env.* file
    from pathlib import Path
    from dotenv import load_dotenv
    ENV = os.getenv("ENV")
    env_file = str(Path(__file__).parents[3] / f'.env.{ENV}')
    load_dotenv(env_file)
    print(f"Loading environment variables from: {env_file}")
    print("working directory is",os.getcwd())

    # # systems
    # systems = get_systems()
    # system_obj = get_system_object('C19WC')

    ## all systems
    # df_systems = get_all_system_objects()
    a = 1


