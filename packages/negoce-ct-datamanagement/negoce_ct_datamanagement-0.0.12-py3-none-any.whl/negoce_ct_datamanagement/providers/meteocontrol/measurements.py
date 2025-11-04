from typing import List, Dict, Tuple
from datetime import datetime, timedelta, time, date, timezone

import numpy as np
import pandas as pd
import asyncio
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus

from negoce_ct_datamanagement.providers.meteocontrol._config import (
    get_api,
    get_api_async
)
from negoce_ct_datamanagement.providers.meteocontrol.sites import (
    get_systems,
    get_nominal_power,
)

semaphore = asyncio.Semaphore(30)  # max 30 requêtes en parallèle


def _normalize(s: str) -> str:
    s = s.lower().replace("$", "")
    for tok in ("_production", "_prod"):
        s = s.replace(tok, "")
    return s.replace("_", " ").strip()

def _chunks(start: datetime, end: datetime, max_days: int):
    cur = start
    while cur < end:
        nxt = min(end, cur + timedelta(days=max_days))
        yield cur, nxt
        cur = nxt

def total_production_timeseries_fine(
    station_names: List[str],
    date_from: datetime,
    date_to: datetime,
    resolution: str = "interval",  # « la plus fine » supportée par basics; sinon 'fifteen-minutes'
    abbreviation: str = "E_Z_EVU",
) -> Tuple[pd.Series, Dict]:
    """
    Retourne la série temporelle agrégée (somme de toutes les stations) à la granularité demandée.
    - Pour resolutions fines (interval, fifteen-minutes, thirty-minutes, hour) → basics par système.
    - Pour day|month|year → endpoint portfolio.
    Ne modifie aucun fichier core.
    """
    if date_from.tzinfo is None: date_from = date_from.replace(tzinfo=timezone.utc)
    if date_to.tzinfo is None:   date_to   = date_to.replace(tzinfo=timezone.utc)
    date_from = date_from.replace(microsecond=0)
    date_to   = date_to.replace(microsecond=0)

    fine_res = {"interval", "fifteen-minutes", "thirty-minutes", "hour"}
    portfolio_res = {"day", "month", "year"}

    if resolution in fine_res:
        max_days = 31
        mode = "per-system-basics"
    elif resolution in portfolio_res:
        max_days = {"day": 60, "month": 365, "year": 365*5}.get(resolution, 60)
        mode = "portfolio"
    else:
        # fallback sûr: on considère fine
        max_days = 31
        mode = "per-system-basics"

    api = get_api()

    # 1) map noms -> systemKey
    systems = get_systems()
    name2key = { _normalize(s["name"]): s["key"] for s in systems if "name" in s and "key" in s }

    matched: Dict[str, str] = {}
    unmatched: List[str] = []

    for original in station_names:
        norm = _normalize(original)
        key = name2key.get(norm)
        if key:
            matched[original] = key
        else:
            # substring fallback
            found = None
            for nm, k in name2key.items():
                if norm in nm or nm in norm:
                    found = k; break
            if found:
                matched[original] = found
            else:
                unmatched.append(original)

    if not matched:
        return pd.Series(dtype=float), {"unmatched": unmatched, "mapped_count": 0, "requests_made": 0, "notes": "no matches"}

    total_by_ts: Dict[str, float] = {}
    requests_made = 1  # 1x /systems

    if mode == "portfolio":
        # 2a) endpoint portfolio: systems/abbreviations/<abbr>/measurements?resolution=day|month|year
        for frm, to in _chunks(date_from, date_to, max_days):
            frm_s = quote_plus(frm.isoformat()); to_s = quote_plus(to.isoformat())
            endpoint = (
                f"systems/abbreviations/{abbreviation}/measurements"
                f"?from={frm_s}&to={to_s}&resolution={resolution}"
            )
            resp = api.send_request(endpoint=endpoint); requests_made += 1
            data = (resp or {}).get("data")
            if isinstance(data, list):
                wanted_keys = set(matched.values())
                for entry in data:
                    sysk = entry.get("systemKey")
                    if sysk not in wanted_keys:
                        continue
                    pts = (entry or {}).get(abbreviation) or []
                    for p in pts:
                        ts = p.get("timestamp"); v = p.get("value")
                        if ts is None or v is None: continue
                        try:
                            total_by_ts[ts] = total_by_ts.get(ts, 0.0) + float(v)
                        except Exception:
                            pass
    else:
        # 2b) per-system basics: systems/<systemKey>/basics/abbreviations/<abbr>/measurements
        wanted = list(matched.values())
        for sysk in wanted:
            for frm, to in _chunks(date_from, date_to, max_days):
                frm_s = quote_plus(frm.isoformat()); to_s = quote_plus(to.isoformat())
                endpoint = (
                    f"systems/{sysk}/basics/abbreviations/{abbreviation}/measurements"
                    f"?from={frm_s}&to={to_s}&resolution={resolution}"
                )
                resp = api.send_request(endpoint=endpoint); requests_made += 1
                data = (resp or {}).get("data")
                # format basics v2: {"data": {"E_Z_EVU": [ {timestamp,value}, ... ]}}
                if isinstance(data, dict):
                    pts = (data or {}).get(abbreviation) or []
                else:
                    pts = []
                for p in pts:
                    ts = p.get("timestamp"); v = p.get("value")
                    if ts is None or v is None: continue
                    try:
                        total_by_ts[ts] = total_by_ts.get(ts, 0.0) + float(v)
                    except Exception:
                        pass

    if not total_by_ts:
        return pd.Series(dtype=float), {
            "unmatched": unmatched,
            "mapped_count": len(matched),
            "requests_made": requests_made,
            "notes": f"no data returned (mode={mode}, resolution={resolution})"
        }

    s = pd.Series({pd.to_datetime(ts, utc=True): val for ts, val in total_by_ts.items()}, dtype=float)
    s = s.sort_index() 


    report = {
        "unmatched": unmatched,
        "mapped_count": len(matched),
        "requests_made": requests_made,
        "notes": f"mode={mode}; resolution={resolution}"
    }
    return s, report


def get_abbreviations() -> List[str]:
    """
    Abbreviations are uppercase strings that identify datapoints.
    """
    api = get_api()
    resp = api.send_request(endpoint="systems/abbreviations")
    return resp['data']

def get_system_measurements(abbreviation_id: str,
                             date_from: datetime,
                             date_to: datetime,
                             resolution: str = 'day'):
    """
    Retrieve measurements for a specific system and abbreviation.

    Parameters:
    - abbreviation_id (str): Measurement type identifier (e.g., 'E_Z_EVU')
    - date_from (datetime): Start date (must be timezone-aware)
    - date_to (datetime): End date (must be timezone-aware)
    - resolution (str): 'day', 'month', or 'year'

    Returns:
    - dict: Raw API response from Meteocontrol
    """
    api = get_api()

    if date_from.tzinfo is None or date_to.tzinfo is None:
        raise ValueError("Datetime objects must include timezone info")

    # Remove microseconds to avoid format issues
    date_from = date_from.replace(microsecond=0)
    date_to = date_to.replace(microsecond=0)

    # Properly URL-encode the ISO strings
    from_str = quote_plus(date_from.isoformat())
    to_str = quote_plus(date_to.isoformat())

    endpoint = (
        f"systems/abbreviations/{abbreviation_id}/measurements"
        f"?from={from_str}&to={to_str}&resolution={resolution}"
    )

    return api.send_request(endpoint=endpoint)

async def test_data_presence(system_key: str, day: datetime) -> dict:
    """
    Return True if system has production data, False otherwise.
    test value on day before to get a full day of measurement
    """
    start = day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=-1)
    end = start + timedelta(days=1)
    state = {
        "value": True,
        "message": None
    }
    try:
        data = await call_bulk_measurements_async(system_key, start, end, resolution='fifteen-minutes')
        if not bool(data and "inverters" in data and data["inverters"]):
            state["value"] = False
            state["message"] = "no inverter data"
    except Exception as e:
        state["value"] = False
        state["message"] = f"[{system_key}] Error while testing data presence for day {day.isoformat()}: {e}"
    return state

async def fetch_system_production(system: dict, start_date: datetime, end_date: datetime):
    """

    """
    production = None
    message = None
    try:
        data_measurements = await call_bulk_measurements_async(system['key'], start_date, end_date, resolution='fifteen-minutes')
        if data_measurements and data_measurements.get('inverters'):
            production = {}
            # system can have multiple inverters
            for dt_str, meters in data_measurements['inverters'].items():
                timestamp = pd.Timestamp(dt_str)
                meter_agg = sum(m.get('E_INT', 0) for m in meters.values() if m.get('E_INT') is not None)
                v = round((meter_agg * 4) / 1000, 3)
                production[timestamp] = v
        else:
            message = {
                "system_key": system['key'],
                "issue": "no inverter data"
            }
    except Exception as e:
        message = {
            "system_key": system['key'],
            "issue": f"{e}"
        }
    finally:
        return {
            'system_name': system['name'],
            'production': production,
            'message': message
        }

async def fetch_production_for_all_systems_async(start_date: datetime, end_date: datetime):
    systems = get_systems()

    # Lancer les tâches en parallèle
    tasks = [
        fetch_system_production(system, start_date, end_date)
        for system in systems
    ]
    results = await asyncio.gather(*tasks)

    # Préparer le DataFrame principal
    dt_range = int((end_date - start_date).total_seconds() / (60 * 15))
    dt_list = [
        (start_date + timedelta(minutes=x * 15)).astimezone(ZoneInfo("Europe/Zurich"))
        for x in range(dt_range)
    ]
    df = pd.DataFrame({"datetime": dt_list})
    errors = {}

    # Utils: somme par ligne en conservant NaN si toutes les sources sont NaN
    def _aggregate(row):
        if row.isnull().all():
            return np.nan
        return round(row.fillna(0).sum(), 3)

    # Injecter la production de chaque système via un merge robuste sur la colonne datetime
    for result in results:
        if result["message"] is not None:
            issue = result["message"]["issue"]
            errors.setdefault(issue, []).append(result["message"]["system_key"])
            continue

        prod_key = f"${result['system_name']}_production"

        # result["production"] attendu comme dict {timestamp: value}
        # -> DataFrame, normalisation TZ et arrondi à la tranche de 15 min
        prod_df = pd.DataFrame(result["production"].items(), columns=["raw_dt", "power_mw"])

        # Parse → UTC → Europe/Zurich → floor 15 min
        prod_df["datetime"] = (
            pd.to_datetime(prod_df["raw_dt"], utc=True, errors="coerce")
              .dt.tz_convert("Europe/Zurich")
              .dt.floor("15min")
        )
        # Retirer les lignes avec datetime invalide
        prod_df = prod_df.dropna(subset=["datetime"])

        # En cas de doublons sur le même pas, agréger
        prod_df = prod_df.groupby("datetime", as_index=False)["power_mw"].sum()

        # Fusion propre; renommer la colonne pour ce système
        df = df.merge(prod_df[["datetime", "power_mw"]], on="datetime", how="left")
        df.rename(columns={"power_mw": prod_key}, inplace=True)

    # Agréger en production_total_mw sans écraser les pas totalement manquants
    value_cols = [c for c in df.columns if c != "datetime" and c.endswith("_production")]
    if value_cols:
        df["production_total_mw"] = df[value_cols].apply(_aggregate, axis=1)
    else:
        df["production_total_mw"] = np.nan

    return df, errors

async def call_bulk_measurements_async(system_key: str, date_from: datetime, date_to: datetime,
                                       resolution: str = "interval", include_interval: int = 0):
    """
    Version asynchrone de call_bulk_measurements
    """
    time_span = date_to - date_from
    if time_span.total_seconds() > 24 * 60 * 60:
        raise ValueError("Maximum time span between from and to is 24 hours")

    endpoint = f"systems/{system_key}/bulk/measurements"
    params = [
        f"from={date_from.strftime("%Y-%m-%dT%H:%M:%S")}",
        f"to={date_to.strftime("%Y-%m-%dT%H:%M:%S")}",
        f"resolution={resolution}",
        f"includeInterval={include_interval}"
    ]
    endpoint = f"{endpoint}?{'&'.join(params)}"

    api = get_api_async()
    try:
        async with semaphore:
            return await api.send_request(endpoint)
    except Exception as e:
        print(f"[async] Error retrieving bulk measurements for system {system_key}: {e}")
        return {}

async def collect_nominal_powers(date: datetime, nominal_powers: dict) -> Tuple[float, float, dict]:
    """
    For all systems:
    - Use provided nominal powers
    - Check data availability (in parallel)
    - Return:
        - Total nominal power
        - Nominal power of systems with data
        - List of system keys without data
    """
    systems = get_systems()
    presence_tasks = [(sys["key"], asyncio.create_task(test_data_presence(sys["key"], date))) for sys in systems]
    await asyncio.gather(*(task for _, task in presence_tasks))

    total_nominal = 0.0
    valid_nominal = 0.0
    missing_keys = {}

    for key, presence_task in presence_tasks:
        nominal = nominal_powers.get(key, 0.0)
        test_data = presence_task.result()
        total_nominal += nominal
        if test_data["value"]:
            valid_nominal += nominal
        else:
            if test_data["message"] not in missing_keys:
                missing_keys[test_data["message"]] = []
            missing_keys[test_data["message"]].append(key)
    # convert data in MW
    total_nominal = round(total_nominal / 1000, 3)
    valid_nominal = round(valid_nominal / 1000, 3)
    return total_nominal, valid_nominal, missing_keys

async def collect_nominal_powers_over_range(start_date: datetime, end_date: datetime) -> List[Tuple[date, float, float, dict]]:
    """
    Calls collect_nominal_powers for each day from start_date to end_date using pre-fetched nominal powers.
    """
    systems = get_systems()

    # Pre-fetch nominal powers once
    nominal_tasks = [(sys["key"], asyncio.create_task(get_nominal_power(sys["key"]))) for sys in systems]
    await asyncio.gather(*(task for _, task in nominal_tasks))
    nominal_powers = {key: task.result() for key, task in nominal_tasks}

    results = []
    current_date = start_date

    while current_date <= end_date:
        print(f"🔄 Processing {current_date.date()}")
        try:
            total, valid, missing = await collect_nominal_powers(current_date, nominal_powers)
            results.append((current_date.date(), total, valid, missing))
        except Exception as e:
            print(f"❌ Error on {current_date.date()}: {e}")
            results.append((current_date.date(), 0.0, 0.0, []))
        current_date += timedelta(days=1)

    return results

if __name__ == '__main__':
    # define env here
    import os
    os.chdir(os.path.dirname(__file__))
    os.environ["ENV"] = "development"
    # load env variables from .env.* file
    from pathlib import Path
    from dotenv import load_dotenv
    ENV = os.getenv("ENV")
    env_file = str(Path(__file__).parents[3] / f'.env.{ENV}')
    load_dotenv(env_file)
    print(f"Loading environment variables from: {env_file}")
    print("working directory is",os.getcwd())

    ## abbreviations
    # abbreviations = get_abbreviations()
    # print(abbreviations) # ['PR', 'G_M', 'E_Z_EVU', 'CO2', 'POWER', 'E_N', 'VFG', 'EPI']

    ## test code
    # fetch all
    d, e = asyncio.run(
        fetch_production_for_all_systems_async(start_date=datetime.combine(datetime.now(), time.min).replace(microsecond=0),
                                               end_date=datetime.now().replace(microsecond=0))
    )
    a = 1
