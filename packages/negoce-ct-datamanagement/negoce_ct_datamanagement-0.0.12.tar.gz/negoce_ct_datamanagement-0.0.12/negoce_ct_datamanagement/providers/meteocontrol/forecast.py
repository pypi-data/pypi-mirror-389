from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
from negoce_ct_datamanagement.providers.meteocontrol._config import (
    get_api,
)

def has_forecast_enabled(system_key: str) -> bool:
    """
    Check if a given system has solar forecast feature enabled.

    Parameters:
    - system_key (str): unique system identifier

    Returns:
    - bool: True if the system has forecast capability, else False
    """
    api = get_api()
    resp = api.send_request(endpoint=f"systems/{system_key}")
    return resp['data'].get('hasSolarForecast', False)

def get_forecast(system_key: str,
                 category: str = None,
                 hours_into_future: int = 48,
                 resolution: str = "fifteen-minutes") -> dict:
    """
    Retrieve production forecast for a given system with optional category.

    Parameters:
    - system_key (str): System identifier
    - category (str): Forecast type (dayAhead | intraday | intradayOptimized)
    - hours_into_future (int): Range of forecast, between 1 and 96
    - resolution (str): 'fifteen-minutes', 'thirty-minutes', or 'hour'

    Returns:
    - dict: API response
    """
    api = get_api()

    query = f"hours_into_future={hours_into_future}&resolution={resolution}"
    if category:
        query += f"&category={category}"

    endpoint = f"systems/{system_key}/forecasts/forecast?{query}"
    return api.send_request(endpoint=endpoint)


def get_specific_energy_forecast(system_key: str,
                                  date_from: datetime,
                                  date_to: datetime) -> dict:
    """
    Fetch specific energy forecast (kWh/kWp) for a given system over a date range.

    Parameters:
    - system_key (str): System identifier
    - date_from (datetime): Start date (timezone-aware, e.g. UTC)
    - date_to (datetime): End date (timezone-aware)

    Returns:
    - dict: API response with projected yield values
    """
    if date_from.tzinfo is None or date_to.tzinfo is None:
        raise ValueError("Datetime parameters must include timezone info")

    # Format and encode dates
    from_str = quote_plus(date_from.replace(microsecond=0).isoformat())
    to_str = quote_plus(date_to.replace(microsecond=0).isoformat())

    endpoint = (
        f"systems/{system_key}/forecasts/yield/specific-energy"
        f"?from={from_str}&to={to_str}"
    )

    api = get_api()
    return api.send_request(endpoint=endpoint)

def get_satellite_irradiance(system_key: str,
                              date_from: datetime,
                              date_to: datetime,
                              resolution: str = "hour") -> dict:
    """
    Fetch satellite-based irradiance data for a given system over a date range.

    Parameters:
    - system_key (str): Unique system identifier
    - date_from (datetime): Start datetime (timezone-aware)
    - date_to (datetime): End datetime (timezone-aware)
    - resolution (str): Optional resolution (e.g. 'fifteen-minutes', 'hour', etc.)

    Returns:
    - dict: API response with irradiance values
    """
    if date_from.tzinfo is None or date_to.tzinfo is None:
        raise ValueError("Datetime parameters must include timezone info")

    # Format and encode date range
    from_str = quote_plus(date_from.replace(microsecond=0).isoformat())
    to_str = quote_plus(date_to.replace(microsecond=0).isoformat())

    # Assemble endpoint with query parameters
    endpoint = (
        f"systems/{system_key}/satellite/irradiance"
        f"?from={from_str}&to={to_str}&resolution={resolution}"
    )

    api = get_api()
    return api.send_request(endpoint=endpoint)
