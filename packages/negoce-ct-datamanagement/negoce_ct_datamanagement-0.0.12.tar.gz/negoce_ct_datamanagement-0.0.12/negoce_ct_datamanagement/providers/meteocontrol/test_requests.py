from __future__ import annotations
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from pathlib import Path
from requests.exceptions import HTTPError
from datetime import datetime, timedelta, timezone, time
import time as pytime
import asyncio
from typing import Dict, Optional, Tuple, Any, List
import logging
import matplotlib
import json
import time as pytime
from requests.exceptions import HTTPError
from zoneinfo import ZoneInfo
from negoce_ct_datamanagement.providers.belvis.meteocontrol import (
    save_meteocontrol_production,
)
from urllib.parse import quote_plus

from negoce_ct_datamanagement.providers.meteocontrol._config import (
    get_api,
    get_api_async
)

os.environ["ENV"] = "development"
env_path = Path(__file__).parents[3] / f".env.{os.getenv('ENV')}"
load_dotenv(env_path)
print(f"[ENV] Loaded environment from: {env_path}")

from negoce_ct_datamanagement.providers.meteocontrol.sites import get_systems
from negoce_ct_datamanagement.providers.meteocontrol.forecast import (
    get_forecast,
    has_forecast_enabled,
    get_specific_energy_forecast,
    get_satellite_irradiance
)
from negoce_ct_datamanagement.providers.meteocontrol.measurements import (
    fetch_production_for_all_systems_async,
    collect_nominal_powers_over_range,
    call_bulk_measurements_async
)
from negoce_ct_datamanagement.providers.meteocontrol._config import get_api_async

from negoce_ct_datamanagement.providers.belvis.requests_utils import (
    read_timeseries_cached,
    ReadOptions,
    read_timeseries,
    read_timeseries_chunked
)

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

def _print_current_limits(resp=None, *, title="📊 Limites API VCOM"):
    """
    Affiche les limites minute/jour à partir:
      1) d'un objet Response (requests/httpx) si fourni
      2) sinon du snapshot mémorisé côté client (_config.get_api / get_api_async)
      3) à défaut: dump TOUTES les en-têtes reçues pour diagnostiquer
    """
    try:
        limits = {}

        # 1) headers d'une réponse passée en paramètre (idéal pour 429)
        if resp is not None and getattr(resp, "headers", None):
            for k, v in resp.headers.items():
                if str(k).lower().startswith("x-ratelimit-"):
                    limits[k] = v

        if not limits:
            # 2) snapshot mémorisé par les clients (sync & async)
            try:
                from negoce_ct_datamanagement.providers.meteocontrol._config import get_api, get_api_async
                api = get_api()
                aapi = get_api_async()
                for src in (getattr(api, "last_limits", None), getattr(aapi, "last_limits", None)):
                    if src:
                        limits.update(src)
            except Exception:
                pass

        if limits:
            print(f"\n{title}")
            for k in sorted(limits.keys()):
                print(f"- {k}: {limits[k]}")
            # Bonus: Retry-After si présent
            ra = None
            if resp is not None and hasattr(resp, "headers"):
                ra = resp.headers.get("Retry-After")
            if ra:
                print(f"- Retry-After: {ra} (secondes ou date)")
            return

        # 3) Rien trouvé ? Dump *tous* les headers de la réponse (diagnostic)
        if resp is not None and getattr(resp, "headers", None):
            print("\n⚠️ Aucune X-RateLimit-* trouvée. Dump de TOUTES les en-têtes reçues :")
            for k, v in resp.headers.items():
                print(f"- {k}: {v}")
        else:
            print("\n⚠️ Aucune information de limite trouvée (pas de headers capturés).")

    except Exception as e:
        print(f"\n⚠️ Impossible de récupérer les limites: {e}")

def _strip_tz_for_excel(df: pd.DataFrame, *, local_tz: str = "Europe/Zurich") -> pd.DataFrame:
    """
    Retourne une copie Excel-compatible:
      - Index (DatetimeIndex ou index objet) => datetime UTC naïf
      - Colonnes datetime64tz => UTC naïf
      - Colonnes object contenant des datetime tz-aware => UTC naïf
    """
    import numpy as np
    out = df.copy()

    # --- Index ---
    if isinstance(out.index, pd.DatetimeIndex):
        if out.index.tz is not None:
            out.index = out.index.tz_convert("UTC").tz_localize(None)
        out.index.name = out.index.name or "timestamp"
    else:
        # Index objet: si ça ressemble à des datetime tz-aware, on convertit
        try:
            idx_series = pd.Series(out.index)
            has_tz = idx_series.map(
                lambda x: isinstance(x, (pd.Timestamp, datetime)) and getattr(x, "tzinfo", None) is not None
            ).any()
            if has_tz:
                out.index = pd.to_datetime(idx_series, utc=True, errors="coerce").dt.tz_localize(None)
                out.index.name = out.index.name or "timestamp"
        except Exception:
            pass

    # --- Colonnes ---
    for c in out.columns:
        s = out[c]
        # 1) dtype datetime64tz
        if pd.api.types.is_datetime64tz_dtype(s):
            out[c] = s.dt.tz_convert("UTC").dt.tz_localize(None)
            continue
        # 2) dtype object: détecter des datetime tz-aware mixtes
        if pd.api.types.is_object_dtype(s):
            try:
                mask = s.map(lambda x: isinstance(x, (pd.Timestamp, datetime)) and getattr(x, "tzinfo", None) is not None)
                if bool(mask.any()):
                    out[c] = pd.to_datetime(s, utc=True, errors="coerce").dt.tz_localize(None)
            except Exception:
                # Laisser tel quel si pas convertible proprement
                pass

    return out
def _ensure_ts_aware(ts: pd.Timestamp) -> pd.Timestamp:
    """Retourne un timestamp *aware* en UTC (si naïf -> on suppose UTC)."""
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")

def _build_top3(df: pd.DataFrame, *, local_tz: str = "Europe/Zurich") -> pd.DataFrame:
    # --- Assurer un index temporel ---
    if not isinstance(df.index, pd.DatetimeIndex):
        # cherche une colonne timestamp candidate
        for cand in ["timestamp", "ts", "time", "local_time", "datetime"]:
            if cand in df.columns:
                ts = pd.to_datetime(df[cand], utc=True, errors="coerce")
                good = ts.notna()
                df = df.loc[good].copy()
                df.index = ts[good]
                # si tu n'as plus besoin de la colonne timestamp, tu peux la drop
                # df.drop(columns=[cand], inplace=True)
                break
        else:
            raise ValueError("Aucune colonne temporelle trouvée (timestamp/ts/time/local_time/date).")

    # tri par temps (sécurité)
    df = df.sort_index()

    # Colonnes candidates
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        exclude = {"timestamp", "ts", "time", "local_time", "datetime"}
        numeric_cols = [c for c in df.columns if c not in exclude]
    print(f"🔍 Found {len(numeric_cols)} numeric columns for Top-3 extraction.")
    rows = []
    for col in numeric_cols:
        s = df[col].dropna()
        idx = pd.to_datetime(s.index, utc=True, errors="coerce")
        bad = idx.isna().sum()
        if bad:
            # on filtre les lignes au timestamp invalide
            s = s[~idx.isna()]
            idx = idx[~idx.isna()]
        s.index = idx
        if s.empty:
            continue

        # Tri décroissant (garde les ex-aequo dans l’ordre d’apparition), puis garde 3
        top = s.nlargest(3, keep="all").head(3)

        for i, (ts, val) in enumerate(top.items(), start=1):
            ts_aware_utc = _ensure_ts_aware(pd.to_datetime(ts))
            ts_local = ts_aware_utc.tz_convert(local_tz)

            rows.append({
                "station": col,
                "rank": i,
                "value": float(val),
                "timestamp_utc": ts_aware_utc,                 # tz-aware (pour CSV -> ISO)
                "timestamp_local": ts_local,                   # tz-aware local (pour CSV -> ISO)
            })

    top3 = pd.DataFrame(rows)
    if top3.empty:
        return top3

    # Colonnes ISO (lisibles dans CSV) + versions naïves (pour Excel)
    top3["timestamp_utc_iso"] = top3["timestamp_utc"].dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    top3["timestamp_local_iso"] = top3["timestamp_local"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    top3["timestamp_utc_naive"] = top3["timestamp_utc"].dt.tz_convert("UTC").dt.tz_localize(None)
    top3["timestamp_local_naive"] = top3["timestamp_local"].dt.tz_localize(None)
    return top3.sort_values(["station", "rank"]).reset_index(drop=True)

def _export_production_results(
    df: pd.DataFrame,
    errors,
    out_dir: str | Path = "outputs",
    base_name: str = "production_results",
    *,
    local_tz: str = "Europe/Zurich"
) -> dict:
    """
    Sauvegarde :
      - *_timeseries.csv : toutes les séries (timestamps + colonnes stations)
      - *_totals.csv     : total par station (kWh) + TOTAL_GLOBAL
      - *_top3.csv       : top 3 pics par station (heure & valeur)
      - *_report.xlsx    : onglets Timeseries / Totals / Top3 / Summary (Excel-safe)
      - *_errors.json    : erreurs éventuelles de collecte
    Retourne les chemins et métriques clés.
    """
    from datetime import datetime

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Génère un préfixe unique pour ce run ---
    run_tag = datetime.now().strftime("%Y%m%d-%H%M%S")

    def _unique_path(p: Path) -> Path:
        """Si p existe, ajoute -001, -002, ... avant l'extension."""
        if not p.exists():
            return p
        stem, suffix = p.stem, p.suffix
        i = 1
        while True:
            candidate = p.with_name(f"{stem}-{i:03d}{suffix}")
            if not candidate.exists():
                return candidate
            i += 1

    # Colonnes numériques présumées = stations
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        exclude = {"timestamp", "ts", "time", "local_time", "date"}
        numeric_cols = [c for c in df.columns if c not in exclude]

    # Totaux par station
    totals = (
        df[numeric_cols]
        .sum(min_count=1)
        .sort_values(ascending=False)
        .rename("energy_kWh")
        .to_frame()
        .reset_index()
        .rename(columns={"index": "station"})
    )
    grand_total = float(totals["energy_kWh"].sum())

    # --- Chemins de sortie *uniques* (avec run_tag) ---
    base_prefix = f"{base_name}_{run_tag}"
    ts_csv   = _unique_path(out_dir / f"{base_prefix}_timeseries.csv")
    tot_csv  = _unique_path(out_dir / f"{base_prefix}_totals.csv")
    top_csv  = _unique_path(out_dir / f"{base_prefix}_top3.csv")
    rep_xlsx = _unique_path(out_dir / f"{base_prefix}_report.xlsx")
    err_json = _unique_path(out_dir / f"{base_prefix}_errors.json")

    # Timeseries CSV (on conserve l’index tel quel)
    non_num_cols = [c for c in df.columns if c not in numeric_cols]
    ordered_cols = non_num_cols + numeric_cols
    df.to_csv(ts_csv, index=True, columns=ordered_cols)

    # Totaux CSV (+ total global en dernière ligne)
    totals.to_csv(tot_csv, index=False)
    with open(tot_csv, "a", encoding="utf-8") as f:
        f.write(f"\nTOTAL_GLOBAL,{grand_total}\n")

    # Top-3 (CSV + onglet Excel)
    top3 = _build_top3(df, local_tz=local_tz)
    if not top3.empty:
        ts_utc_naive   = top3["timestamp_utc"].dt.tz_convert("UTC").dt.tz_localize(None)
        ts_local_naive = top3["timestamp_local"].dt.tz_localize(None)
        ts_utc_naive   = ts_utc_naive.where(ts_utc_naive.notna(), None)
        ts_local_naive = ts_local_naive.where(ts_local_naive.notna(), None)
        top3_xl = pd.DataFrame({
            "station": top3["station"],
            "rank": top3["rank"].astype(int),
            "value": top3["value"].astype(float),
            "timestamp_utc":  ts_utc_naive.dt.to_pydatetime() if hasattr(ts_utc_naive, "dt") else ts_utc_naive,
            "timestamp_local": ts_local_naive.dt.to_pydatetime() if hasattr(ts_local_naive, "dt") else ts_local_naive,
        })
    else:
        top3_xl = pd.DataFrame(columns=["station", "rank", "value", "timestamp_utc", "timestamp_local"])

    # --- Versions Excel-safe ---
    df_xl = _strip_tz_for_excel(df, local_tz=local_tz)
    totals_xl = totals.copy()
    summary_xl = pd.DataFrame(
        {"metric": ["stations_count", "rows", "grand_total_kWh", "export_time_utc", "run_tag"],
         "value": [len(numeric_cols), len(df), grand_total, pd.Timestamp.utcnow().isoformat(), run_tag]}
    )

    with pd.ExcelWriter(rep_xlsx, engine="openpyxl") as xw:
        df_xl.to_excel(xw, sheet_name="Timeseries", index=True)
        totals_xl.to_excel(xw, sheet_name="Totals", index=False)
        top3_xl.to_excel(xw, sheet_name="Top3", index=False)
        summary_xl.to_excel(xw, sheet_name="Summary", index=False)

    # Erreurs éventuelles
    if errors:
        try:
            with open(err_json, "w", encoding="utf-8") as f:
                json.dump(errors, f, ensure_ascii=False, indent=2)
        except Exception:
            err_json = None

    return {
        "timeseries_csv": str(ts_csv),
        "totals_csv": str(tot_csv),
        "top3_csv": str(top_csv),
        "report_xlsx": str(rep_xlsx),
        "errors_json": str(err_json) if errors else None,
        "grand_total_kWh": grand_total,
        "stations_count": len(numeric_cols),
        "run_tag": run_tag,
    }

def start_http_counter():
    """
    Patch 'requests.sessions.Session.request' (sync) et 'httpx.AsyncClient.request' (async)
    pour compter TOUTES les requêtes (GET/POST), y compris /login et les retries.
    Retourne (counters, restore) où restore() enlève le patch.
    """
    import requests, httpx
    from types import SimpleNamespace

    counters = {
        "total": 0,
        "requests_get": 0,
        "requests_post": 0,
        "httpx_get": 0,
        "httpx_post": 0,
        "login_calls": 0,
    }

    orig = SimpleNamespace(
        requests_request = requests.sessions.Session.request,
        httpx_request    = httpx.AsyncClient.request
    )

    def _is_login(url) -> bool:
        try:
            return str(url).rstrip("/").endswith("/login")
        except Exception:
            return False

    def _requests_request_wrapper(self, method, url, *args, **kwargs):
        m = (method or "").upper()
        counters["total"] += 1
        if m == "GET":
            counters["requests_get"] += 1
        elif m == "POST":
            counters["requests_post"] += 1
        if _is_login(url):
            counters["login_calls"] += 1
        return orig.requests_request(self, method, url, *args, **kwargs)

    async def _httpx_request_wrapper(self, method, url, *args, **kwargs):
        m = (method or "").upper()
        counters["total"] += 1
        if m == "GET":
            counters["httpx_get"] += 1
        elif m == "POST":
            counters["httpx_post"] += 1
        if _is_login(url):
            counters["login_calls"] += 1
        return await orig.httpx_request(self, method, url, *args, **kwargs)

    # Patch (niveau le plus bas = pas de double comptage)
    import requests, httpx  # re-import safe
    requests.sessions.Session.request = _requests_request_wrapper
    httpx.AsyncClient.request = _httpx_request_wrapper

    def restore():
        requests.sessions.Session.request = orig.requests_request
        httpx.AsyncClient.request = orig.httpx_request

    return counters, restore

def print_http_counters(counters, title="📡 Compteur de requêtes HTTP"):
    print(f"\n{title}")
    print(f"- Total            : {counters['total']}")
    print(f"  • requests  GET  : {counters['requests_get']}")
    print(f"  • requests  POST : {counters['requests_post']}")
    print(f"  • httpx     GET  : {counters['httpx_get']}")
    print(f"  • httpx     POST : {counters['httpx_post']}")
    print(f"  • appels /login  : {counters['login_calls']}")

def test_forecast_specific():
    """
    Teste les combinaisons category / hours_into_future / resolution
    sur le système AX8J6 (SS12_Longirod).
    """
    import itertools

    system_key = "AX8J6"
    categories = ["dayAhead", "intraday", "intradayOptimized"]
    hours_into_future_values = [24, 48, 72, 96]
    resolutions = ["fifteen-minutes", "thirty-minutes", "hour"]

    all_combinations = list(itertools.product(categories, hours_into_future_values, resolutions))
    total = len(all_combinations)
    success_count = 0

    print(f"🔍 Test de {total} combinaisons possibles sur le système {system_key}")

    for i, (cat, h, res) in enumerate(all_combinations, 1):
        print(f"\n➡️ [{i}/{total}] Catégorie={cat}, h={h}, résolution={res}")
        try:
            data = get_forecast(
                system_key,
                category=cat,
                hours_into_future=h,
                resolution=res
            )
            print("✅ Succès")
            print(data[:1])  # Affiche juste un exemple
            success_count += 1
        except HTTPError as e:
            print(f"❌ HTTP {e.response.status_code} - {e.response.reason}")
        except Exception as ex:
            print(f)



def test_forecast():
    """
    Unsuccessfull

    Test the forecast functionality by fetching and displaying forecast data for available systems.

    Expected output:
    - Forecast data for each system for the acutal month in each of the following categories:
      - dayAhead
      - intraday
      - intradayOptimized
    - Summary of systems with forecast enabled/disabled

    Effective output:
    - Response from API: HTTP Error: 403 - System does't have forecast feature.
    - Systems info:
      - Total systèmes: 102
      - Systèmes avec prévisions activées: 83
      - Systèmes sans prévisions activées: 19
      - Prévisions réussies: 0

    """
    print("🔍 Récupération des systèmes disponibles...")
    systems = get_systems()
    if not systems:
        print("❌ Aucun système trouvé.")
        return
    print(f"✅ {len(systems)} systèmes trouvés. Exemple: {systems[0]}")

    # Step 2: Find the first system with forecast enabled
    selected_system = None
    count_forecast_disabled = 0
    count_forecast_enabled = 0
    count_succeded = 0
    for system in systems:
        if has_forecast_enabled(system["key"]):
            count_forecast_enabled += 1
            selected_system = system
            # Step 3: Fetch and display forecast
            print(f"\n📡 Selected system: {selected_system['name']} (key: {selected_system['key']})")
            print("🔮 Fetching forecast data...")
            categories = ["dayAhead", "intraday", "intradayOptimized"]

            for cat in categories:
                print(f"🧪 Testing forecast category: {cat}")
                try:
                    forecast_data = get_forecast(system["key"], category=cat)
                    print(f"✅ Forecast for category '{cat}':")
                    print(forecast_data)
                    count_succeded += 1
                    break  # Stop at first successful category
                except HTTPError as e:
                    if e.response.status_code == 403:
                        print(f"🚫 Category '{cat}' not allowed for this system.")
                    else:
                        print(f"❌ Error for category '{cat}': {e}")
        else:
            count_forecast_disabled += 1
        

        # try:
        #     date_from = datetime.now(timezone.utc).replace(day=1)
        #     date_to = date_from + timedelta(days=31)  # au moins un mois
        #     print(f"\n📅 Récupération des prévisions d'énergie spécifique pour la période {date_from} à {date_to}...")

        #     specific_energy_data = get_specific_energy_forecast(
        #         system["key"],
        #         date_from=date_from,
        #         date_to=date_to
        # )
        #     print("🔋 Specific Energy Forecast:")
        #     print(specific_energy_data)
        # except HTTPError as e:
        #     if e.response.status_code == 403:
        #         print("🚫 Specific Energy Forecast is not available for this system (403 Forbidden).")
        #     if e.response.status_code == 429:
        #         print("⏳ Hit request limit — waiting 30 seconds...")
        #         pytime.sleep(30)
        #         continue  # retry with next system
        #     else:
        #         print(f"❌ HTTP error while fetching forecast: {e}")

    if not selected_system:
        print("❌ No system with forecast capability found.")
        exit(1)
    print(f"\n📊 Résumé des systèmes :"
          f"\n- Total systèmes: {len(systems)}"
          f"\n- Systèmes avec prévisions activées: {count_forecast_enabled}"
          f"\n- Systèmes sans prévisions activées: {count_forecast_disabled}"
          f"\n- Prévisions réussies: {count_succeded}")

def specific_energy_value_consistency():
    """
    Successfull

    Vérifie que les valeurs d'énergie spécifique pour un système donné soient inchangées entre deux appels.

    System key: "27D4V"
    Date range: 01.06.2025 to 01.07.2025

    Expected output:
      - same value for specific energy forecast on two consecutive calls

    Effective output:
      - same value.
    """

    key = "27D4V"
    print(f"🔍 Vérification des prévisions pour le système {key}...")
    while True:
        if has_forecast_enabled(key):
            print(f"✅ Le système {key} a les prévisions activées.")
        try:
            date_from = datetime.now(timezone.utc).replace(day=1)
            date_to = date_from + timedelta(days=31)  # au moins un mois
            print(f"\n📅 Récupération des prévisions d'énergie spécifique pour la période {date_from} à {date_to}...")

            specific_energy_data = get_specific_energy_forecast(
                key,
                date_from=date_from,
                date_to=date_to
            )
            print("🔋 Specific Energy Forecast:")
            print(specific_energy_data)
        except HTTPError as e:
            if e.response.status_code == 403:
                print("🚫 Specific Energy Forecast is not available for this system (403 Forbidden).")
            if e.response.status_code == 429:
                print("⏳ Hit request limit — waiting 30 seconds...")
                pytime.sleep(30)
            else:
                print(f"❌ HTTP error while fetching forecast: {e}")

def specific_energy_minimal_date():
    """
    Successfull
    
    Check for the minimal date for specific energy forecast for a given system.

    System key: "27D4V"
    Date range: tested with different date ranges

    Expected output:
    - Specific Energy Forecast with the smallest date range
    - Graphical representation

    Effective output:
    - series of specific energy forecast values by month
    """

    key = "27D4V"
    print(f"🔍 Vérification des prévisions pour le système {key}...")
    date_from = datetime.now(timezone.utc).replace(day=11)
    date_to = date_from + timedelta(days=3300)
    print(f"Date de début: {date_from}")
    print(f"Date de fin: {date_to}")

    if has_forecast_enabled(key):
        print(f"✅ Le système {key} a les prévisions activées.")
    try:
        print(f"\n📅 Récupération des prévisions d'énergie spécifique pour la période {date_from} à {date_to}...")

        specific_energy_data = get_specific_energy_forecast(
            key,
            date_from=date_from,
            date_to=date_to
        )
        print("🔋 Specific Energy Forecast:")
        print(specific_energy_data)

        # Visualisation
        data = specific_energy_data.get("data", [])
        if not data:
            print("⚠️ Aucune donnée de prévision disponible.")
            return

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df["value"], marker='o', linestyle='-')
        plt.title("Prévision d'énergie spécifique mensuelle")
        plt.xlabel("Date")
        plt.ylabel("Énergie spécifique (kWh/kWp)")
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(rotation=45)
        plt.savefig("specific_energy_forecast2png")
        print("📸 Graphique sauvegardé sous 'specific_energy_forecast.png'")


    except HTTPError as e:
        if e.response.status_code == 403:
            print("🚫 Specific Energy Forecast is not available for this system (403 Forbidden).")
        elif e.response.status_code == 429:
            print("⏳ Hit request limit — waiting 30 seconds...")
            pytime.sleep(30)
        else:
            print(f"❌ HTTP error while fetching forecast: {e}")

def specific_energy_minimal_date_superposed():
    """
    Successfull
    
    Compares energy curve forecast by year

    System key: "27D4V"
    Date range: tested with 1 xear and 10 years

    Expected output:
    - Graphical representation of variations

    Effective output:
    - No variations
    """

    key = "27D4V"
    print(f"🔍 Vérification des prévisions pour le système {key}...")
    date_from = datetime.now(timezone.utc).replace(day=11)
    date_to = date_from + timedelta(days=3300)
    print(f"Date de début: {date_from}")
    print(f"Date de fin: {date_to}")

    if has_forecast_enabled(key):
        print(f"✅ Le système {key} a les prévisions activées.")

    try:
        print(f"\n📅 Récupération des prévisions d'énergie spécifique pour la période {date_from} à {date_to}...")

        specific_energy_data = get_specific_energy_forecast(
            key,
            date_from=date_from,
            date_to=date_to
        )
        print("🔋 Specific Energy Forecast:")
        print(specific_energy_data)

        # Visualisation
        data = specific_energy_data.get("data", [])
        if not data:
            print("⚠️ Aucune donnée de prévision disponible.")
            return

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["year"] = df["timestamp"].dt.year
        df["month_day"] = df["timestamp"].apply(lambda x: x.replace(year=2000))

        # Création du graphique
        plt.figure(figsize=(12, 6))
        for year, group in df.groupby("year"):
            plt.plot(group["month_day"], group["value"], marker='o', label=str(year))

        plt.title("Prévision d'énergie spécifique - Comparaison annuelle")
        plt.xlabel("Mois")
        plt.ylabel("Énergie spécifique (kWh/kWp)")
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        plt.legend(title="Année")
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(rotation=45)
        plt.savefig("specific_energy_forecast.png")
        print("📸 Graphique sauvegardé sous 'specific_energy_forecast.png'")

    except HTTPError as e:
        if e.response.status_code == 403:
            print("🚫 Specific Energy Forecast is not available for this system (403 Forbidden).")
        elif e.response.status_code == 429:
            print("⏳ Hit request limit — waiting 30 seconds...")
            pytime.sleep(30)
        else:
            print(f"❌ HTTP error while fetching forecast: {e}")

def specific_energy_compare_all_systems():
    """
    Successfull
    
    Compares energy curve forecast by system

    System key: all
    Date range: tested with 10 years and 1 year

    Expected output:
    - Graphical representation of variations between systems
    - Minimum and maximum values among all systems

    Effective output:
    - Small varations between systems
    - Same vartions for all years
    """
        
    systems = get_systems()
    if not systems:
        print("❌ Aucun système disponible.")
        return

    # Définir la période de prévision commune
    date_from = datetime.now(timezone.utc).replace(day=11)
    date_to = date_from + timedelta(days=3650)

    print(f"📆 Période de prévision : {date_from.date()} à {date_to.date()}")
    plt.figure(figsize=(14, 7))

    min_value = float("inf")
    max_value = float("-inf")
    min_system = ""
    max_system = ""


    for system in systems:
        key = system["key"]
        name = system["name"]

        if not has_forecast_enabled(key):
            continue

        print(f"📡 {name} ({key}) — Prévisions activées")

        try:
            specific_energy_data = get_specific_energy_forecast(
                key,
                date_from=date_from,
                date_to=date_to
            )
            data = specific_energy_data.get("data", [])
            if not data:
                print(f"⚠️ Aucune donnée pour {name}")
                continue

            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)

            # Trouver les extrêmes de ce système
            local_min = df["value"].min()
            local_max = df["value"].max()

            if local_min < min_value:
                min_value = local_min
                min_system = name

            if local_max > max_value:
                max_value = local_max
                max_system = name

            # Tracer la courbe pour ce système
            plt.plot(df.index, df["value"], label=name)

        except HTTPError as e:
            if e.response.status_code == 403:
                print(f"🚫 Accès interdit aux prévisions pour {name}")
            elif e.response.status_code == 429:
                print("⏳ Limite atteinte — attente de 30 secondes...")
                pytime.sleep(30)
                continue
            else:
                print(f"❌ Erreur HTTP pour {name}: {e}")

    plt.title("Comparaison des prévisions d'énergie spécifique par système")
    plt.xlabel("Date")
    plt.ylabel("Énergie spécifique (kWh/kWp)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend(loc='upper right', fontsize='small')
    plt.tight_layout()
    plt.savefig("compare_specific_energy_all_systems3.png")
    print("📸 Graphique sauvegardé sous 'compare_specific_energy_all_systems.png'")
    print(f"\n📉 Valeur minimale : {min_value:.2f} kWh/kWp ({min_system})")
    print(f"📈 Valeur maximale : {max_value:.2f} kWh/kWp ({max_system})")

def test_satellite_irradiance():
    """
    Successfull but off topic (no forecast)
    
    Test the satellite irradiance data retrieval for all systems.
    
    Date: 3 days from now
    
    Expected output:
        - Successful retrieval of irradiance data for each system
    Effective output:
        - Data retrieved for each system
    """
        
    print("🌞 Test des données d'irradiation satellite...")

    systems = get_systems()
    if not systems:
        print("❌ Aucun système trouvé.")
        return

    count_success = 0
    count_failed = 0

    # Date range sur 3 jours
    date_from = datetime.now(timezone.utc) - timedelta(days=3)
    date_to = datetime.now(timezone.utc)

    for system in systems:
        print(f"\n📡 Système: {system['name']} (key: {system['key']})")
        try:
            data = get_satellite_irradiance(
                system_key=system["key"],
                date_from=date_from,
                date_to=date_to,
                resolution="hour"
            )
            print("✅ Données d'irradiance récupérées.")
            print(data)
            count_success += 1

        except HTTPError as e:
            if e.response.status_code == 403:
                print("🚫 Accès refusé aux données d'irradiance pour ce système (403 Forbidden).")
            elif e.response.status_code == 429:
                print("⏳ Limite de requêtes atteinte (429). Pause de 30 secondes...")
                pytime.sleep(30)
                continue  # passer au suivant après pause
            else:
                print(f"❌ Erreur HTTP inattendue: {e}")
            count_failed += 1

    print(f"\n📊 Résumé:")
    print(f"- Total systèmes testés: {len(systems)}")
    print(f"- Succès: {count_success}")
    print(f"- Échecs: {count_failed}")

def test_single_satellite_irradiance():

    """
    Successfull but off topic (no forecast)
    
    Test the satellite irradiance data retrieval for specific system with vizualisation.
    
    Date: 3 days from now
    
    Expected output:
        - Successful retrieval of irradiance data by hour
    Effective output:
        - Data retrieved by hour
    """

    key = "27D4V"
    print(f"🔍 Vérification de l'irradiation satellite pour le système {key}...")

    date_from = datetime.now(timezone.utc) - timedelta(days=3)
    date_to = datetime.now(timezone.utc) + timedelta(days=3)
    print(f"🗓️ Intervalle: {date_from} → {date_to}")

    try:
        irradiance_data = get_satellite_irradiance(
            system_key=key,
            date_from=date_from,
            date_to=date_to,
            resolution="hour"
        )
        print("☀️ Données d'irradiance récupérées:")
        print(irradiance_data)

        data = irradiance_data.get("data", [])
        if not data:
            print("⚠️ Aucune donnée trouvée.")
            return

        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df["value"], marker='o', linestyle='-')
        plt.title("Irradiation satellite (3 derniers jours)")
        plt.xlabel("Heure")
        plt.ylabel("Irradiance (W/m²)")
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %Hh'))
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("satellite_irradiance_forecast.png")
        print("📸 Graphique sauvegardé sous 'satellite_irradiance_forecast.png'")

    except HTTPError as e:
        if e.response.status_code == 403:
            print("🚫 L'accès aux données d'irradiance est interdit pour ce système.")
        elif e.response.status_code == 429:
            print("⏳ Trop de requêtes — pause de 30s.")
            pytime.sleep(30)
        else:
            print(f"❌ Erreur HTTP: {e}")

def playground():
    print("🔍 Récupération des systèmes disponibles...")
    systems = get_systems()
    if not systems:
        print("❌ Aucun système trouvé.")
        return
    print(f"✅ {len(systems)} systèmes trouvés. Exemple: {systems[0]}")

    selected_system = None
    count_forecast_disabled = 0
    count_forecast_enabled = 0
    count_succeded = 0
    for system in systems:
        if has_forecast_enabled(system["key"]):
            count_forecast_enabled += 1
        else:
            count_forecast_disabled += 1
        selected_system = system
        
        print(f"\n📡 Selected system: {selected_system['name']} (key: {selected_system['key']})")
        print("🔮 Fetching forecast data...")
        categories = ["dayAhead", "intraday", "intradayOptimized"]

        for cat in categories:
            print(f"🧪 Testing forecast category: {cat}")
            try:
                forecast_data = get_forecast(system["key"], category=cat)
                print(f"✅ Forecast for category '{cat}':")
                print(forecast_data)
                count_succeded += 1
                break  # Stop at first successful category
            except HTTPError as e:
                if e.response.status_code == 403:
                    print(f"🚫 Category '{cat}' not allowed for this system.")
                else:
                    print(f"❌ Error for category '{cat}': {e}")

        try:
            date_from = datetime.now(timezone.utc).replace(day=1)
            date_to = date_from + timedelta(days=31)  # au moins un mois
            print(f"\n📅 Récupération des prévisions d'énergie spécifique pour la période {date_from} à {date_to}...")

            specific_energy_data = get_specific_energy_forecast(
                system["key"],
                date_from=date_from,
                date_to=date_to
        )
            print("🔋 Specific Energy Forecast:")
            print(specific_energy_data)
        except HTTPError as e:
            if e.response.status_code == 403:
                print("🚫 Specific Energy Forecast is not available for this system (403 Forbidden).")
            if e.response.status_code == 429:
                print("⏳ Hit request limit — waiting 30 seconds...")
                pytime.sleep(30)
                continue  # retry with next system
            else:
                print(f"❌ HTTP error while fetching forecast: {e}")

    if not selected_system:
        print("❌ No system with forecast capability found.")
        exit(1)
    print(f"\n📊 Résumé des systèmes :"
          f"\n- Total systèmes: {len(systems)}"
          f"\n- Systèmes avec prévisions activées: {count_forecast_enabled}"
          f"\n- Systèmes sans prévisions activées: {count_forecast_disabled}"
          f"\n- Prévisions réussies: {count_succeded}")
    
async def test_speed_fetch_production_for_all_systems():
    """
    Boucle jour par jour sur 3 mois glissants (de J-3 mois à hier, en heure locale Europe/Zurich),
    appelle fetch_production_for_all_systems_async pour chaque fenêtre de 24h (borne haute exclusive),
    additionne les résultats, exporte un rapport unique et affiche les compteurs HTTP.

    - Gestion 429: retry exponentiel simple (jusqu'à 3 tentatives/jour).
    - Les bornes journalières sont construites en Europe/Zurich puis converties en UTC.
    """
    import requests, httpx
    import pandas as pd
    from pandas.tseries.offsets import DateOffset

    TZ_LOCAL = "Europe/Zurich"
    print("⏱️ Lancement multi-jours (3 mois → hier) ...")

    # ---------- Compteurs HTTP globaux ----------
    counters = {
        "total": 0,
        "requests_get": 0,
        "requests_post": 0,
        "httpx_get": 0,
        "httpx_post": 0,
        "login_calls": 0,
    }

    _orig_requests_get = requests.get
    _orig_requests_post = requests.post
    _orig_httpx_get = httpx.AsyncClient.get
    _orig_httpx_post = httpx.AsyncClient.post

    def _extract_url(args, kwargs):
        if kwargs and "url" in kwargs:
            return kwargs["url"]
        return args[0] if args else None

    def _requests_get_wrapper(*args, **kwargs):
        counters["total"] += 1
        counters["requests_get"] += 1
        return _orig_requests_get(*args, **kwargs)

    def _requests_post_wrapper(*args, **kwargs):
        url = _extract_url(args, kwargs)
        counters["total"] += 1
        counters["requests_post"] += 1
        if url and str(url).endswith("/login"):
            counters["login_calls"] += 1
        return _orig_requests_post(*args, **kwargs)

    async def _httpx_get_wrapper(self, *args, **kwargs):
        counters["total"] += 1
        counters["httpx_get"] += 1
        return await _orig_httpx_get(self, *args, **kwargs)

    async def _httpx_post_wrapper(self, *args, **kwargs):
        url = _extract_url(args, kwargs)
        counters["total"] += 1
        counters["httpx_post"] += 1
        if url and str(url).endswith("/login"):
            counters["login_calls"] += 1
        return await _orig_httpx_post(self, *args, **kwargs)

    # Patch
    requests.get = _requests_get_wrapper
    requests.post = _requests_post_wrapper
    httpx.AsyncClient.get = _httpx_get_wrapper
    httpx.AsyncClient.post = _httpx_post_wrapper

    # ---------- Fenêtre 3 mois (locale) ----------
    now_local_midnight = pd.Timestamp.now(tz=TZ_LOCAL).normalize()

    # CHANGEMENT: vrai "3 mois → hier" (borne haute exclusive = aujourd'hui 00:00)
    start_local = pd.Timestamp(2025, 10, 26, 23, 0, 0, tz=TZ_LOCAL)
    end_local_excl = pd.Timestamp(2025, 10, 27, 21, 59, 0, tz=TZ_LOCAL)

    # Liste des jours [start_local, end_local_excl) pas de 1 jour (tz-aware)
    days_local = pd.date_range(start=start_local, end=end_local_excl, freq="D", inclusive="left")

    print(f"📆 Période locale: {start_local.date()} → {(end_local_excl - pd.Timedelta(days=1)).date()} (inclus) — {len(days_local)} jours")

    # ---------- Boucle jour par jour ----------
    frames = []
    collected_errors = {}
    total_elapsed = 0.0

    try:
        for i, d_local in enumerate(days_local, 1):
            # CHANGEMENT: fenêtres journalières propres [00:00, 24:00) (pas de -1 minute)
            day_start_local = d_local.replace(hour=7, minute=0, second=0, microsecond=0)
            day_end_local   = (d_local + pd.Timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)

            start_utc = day_start_local.tz_convert("UTC").to_pydatetime()
            end_utc   = day_end_local.tz_convert("UTC").to_pydatetime()

            print(f"\n➡️  [{i}/{len(days_local)}] {day_start_local.date()}  (UTC: {start_utc} → {end_utc} exclu)")

            # Retry simple sur 429
            max_retries = 3
            backoff = 15  # secondes
            attempt = 0
            while True:
                attempt += 1
                start_time = pytime.time()
                try:
                    df_day, errors_day = await fetch_production_for_all_systems_async(
                        start_date=start_utc,
                        end_date=end_utc,  # borne haute exclusive
                    )
                    elapsed = pytime.time() - start_time
                    total_elapsed += elapsed

                    # Empilement
                    if df_day is not None and not df_day.empty:
                        frames.append(df_day)
                        print(f"✅ Jour collecté. Colonnes: {df_day.shape[1]} | Lignes: {len(df_day)} | {elapsed:.2f}s")
                    else:
                        print(f"⚠️ Jour sans données (DataFrame vide). {elapsed:.2f}s")

                    if errors_day:
                        collected_errors[str(day_start_local.date())] = errors_day
                        print(f"🔎 Erreurs jour {day_start_local.date()}: {len(errors_day)}")

                    break  # OK -> prochain jour

                except HTTPError as e:
                    code = getattr(e.response, "status_code", None)
                    reason = getattr(e.response, "reason", "")
                    print(f"❌ HTTP {code} {reason} (tentative {attempt}/{max_retries})")
                    _print_current_limits(e.response)

                    if code == 429 and attempt < max_retries:
                        wait_s = backoff * attempt
                        print(f"⏳ 429 — pause {wait_s}s puis retry...")
                        pytime.sleep(wait_s)
                        continue
                    else:
                        collected_errors[str(day_start_local.date())] = {"http_error": f"{code} {reason}"}
                        break

                except Exception as ex:
                    print(f"❌ Exception inattendue sur {day_start_local.date()}: {ex}")
                    collected_errors[str(day_start_local.date())] = {"exception": str(ex)}
                    break

            if i % 2 == 0 and i != len(days_local):
                print("⏳ Pause de 32 secondes (throttle toutes les 2 itérations)...")
                pytime.sleep(32)

        # ---------- Concaténation + export ----------
        if frames:
            df_all = pd.concat(frames, axis=0, ignore_index=True)

            # Tri par temps si colonne 'datetime' présente
            if "datetime" in df_all.columns:
                df_all = df_all.sort_values("datetime")

            export_info = _export_production_results(
                df=df_all,
                errors=collected_errors,
                out_dir="outputs",
                base_name="production_results_3months_daily",
                local_tz=TZ_LOCAL,
            )

            print("\n📦 Export global :")
            print(f"- Timeseries CSV : {export_info['timeseries_csv']}")
            print(f"- Totaux CSV     : {export_info['totals_csv']}")
            print(f"- Rapport Excel  : {export_info['report_xlsx']}")
            if export_info.get("errors_json"):
                print(f"- Erreurs JSON   : {export_info['errors_json']}")
            print(f"🌐 Total global  : {export_info['grand_total_kWh']:.3f} kWh  | Stations: {export_info['stations_count']}")
            print(f"⏲️ Temps cumulé  : {total_elapsed:.2f}s  | Jours traités: {len(frames)}")

        else:
            print("❌ Aucun jour n'a pu être collecté, pas d'export.")

        # ---------- Compteurs HTTP ----------
        print("\n📡 Compteur de requêtes HTTP (3 mois) ")
        print(f"- Total            : {counters['total']}")
        print(f"  • requests  GET  : {counters['requests_get']}")
        print(f"  • requests  POST : {counters['requests_post']}")
        print(f"  • httpx     GET  : {counters['httpx_get']}")
        print(f"  • httpx     POST : {counters['httpx_post']}")
        print(f"  • appels /login  : {counters['login_calls']}")

    finally:
        # Restore
        requests.get = _orig_requests_get
        requests.post = _orig_requests_post
        httpx.AsyncClient.get = _orig_httpx_get
        httpx.AsyncClient.post = _orig_httpx_post

        

def test_speed_fetch_production_for_all_systems_sync():
    """
    Teste la vitesse de récupération des données de production pour tous les systèmes (version synchrone).
    """
    print("⏱️ Test sync de la vitesse de récupération des données de production pour tous les systèmes...")
    start_time = pytime.time()

    try:
        from negoce_ct_datamanagement.providers.meteocontrol.measurements import fetch_production_for_all_systems

        start = datetime.combine(datetime.now() - timedelta(days=2), time(hour=12)).replace(microsecond=0)
        end = start + timedelta(hours=8)

        df, errors = fetch_production_for_all_systems(
            start_date=start,
            end_date=end
        )

        elapsed_time = pytime.time() - start_time
        print(f"✅ Données de production récupérées pour {df.shape[1] - 2} systèmes en {elapsed_time:.2f} secondes.")
        print("🔎 Erreurs :", errors if errors else "Aucune")
        print(df.head())

    except HTTPError as e:
        if e.response.status_code == 403:
            print("🚫 Accès interdit aux données de production (403 Forbidden).")
        elif e.response.status_code == 429:
            print("⏳ Limite de requêtes atteinte (429). Pause de 30 secondes...")
            pytime.sleep(30)
        else:
            print(f"❌ Erreur HTTP inattendue: {e}")
    except Exception as e:
        print(f"❌ Exception inattendue : {e}")

def compare_speed_fetch_production():
    """
    Compare la vitesse de récupération des données de production entre les versions synchrone et asynchrone.
    """
    print("🔍 Comparaison de la vitesse de récupération des données de production...")
    print("1. Version synchrone")
    test_speed_fetch_production_for_all_systems_sync()
    print("\n2. Version asynchrone")
    asyncio.run(test_speed_fetch_production_for_all_systems())

async def test_collect_nominal_powers_over_one_month():
    """
    Test the function collect_nominal_powers_over_range for a 1-month interval in the past.
    Uses naive datetimes (no timezone).
    """
    # Get today's date
    today = datetime.today()

    # Define a 1-month period in the past (previous calendar month)
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
    start_date = last_day_of_last_month.replace(day=24)
    end_date = last_day_of_last_month

    print(f"▶ Testing from {start_date.date()} to {end_date.date()}")

    # Call the function
    results = await collect_nominal_powers_over_range(start_date, end_date)

    # Print the results
    for day, total, valid, missing in results:
        print(f"{day}: Total={total:.2f} kWp, Valid={valid:.2f} kWp, Missing={len(missing)} systems")

async def test_latest_realized_per_system_async(top_n: int = 10):
    """
    Liste les stations triées par 'technical-data/last-data-input' (async)
    et affiche le nombre total de requêtes HTTP, même en cas d'erreur 429.
    """
    counters, restore = start_http_counter()
    try:
        from negoce_ct_datamanagement.providers.meteocontrol.sites import get_systems
        from negoce_ct_datamanagement.providers.meteocontrol._config import get_api_async
        from requests.exceptions import HTTPError

        systems = get_systems()
        api = get_api_async()
        rows = []

        async def fetch_last(system):
            key = system["key"]; name = system["name"]
            try:
                data = await api.send_request(f"systems/{key}/technical-data/last-data-input")
                ts = (data or {}).get("data", {}).get("timestamp")
                rows.append({"system_key": key, "system_name": name, "last_data_input": ts})
                print(f"• {name} ({key}) → {ts}")
            except HTTPError as e:
                code = getattr(e.response, "status_code", "?")
                print(f"❌ {name} ({key}) HTTP {code}")
            except Exception as e:
                print(f"❌ {name} ({key}) {e}")

        await asyncio.gather(*(fetch_last(s) for s in systems))

        if not rows:
            print("❌ Aucune donnée 'last-data-input' récupérée.")
            return

        df = pd.DataFrame(rows).sort_values("last_data_input", ascending=False, na_position="last")
        print("\n🏁 TOP stations les plus fraîches :")
        print(df.head(top_n).to_string(index=False))

    finally:
        # Affiche TOUJOURS le compteur, même en cas d'erreur/429
        print_http_counters(counters, title="📡 (last-data-input) Compteur de requêtes HTTP")
        restore()

async def test_latest_realized_per_inverter_async(hours_back: int = 24, per_system_top: int = 10):
    """
    Pour chaque station, liste les onduleurs triés par dernier timestamp E_INT non-nul
    et affiche le nombre total de requêtes HTTP, même en cas d'erreur de dépassement.
    """
    counters, restore = start_http_counter()
    try:
        from negoce_ct_datamanagement.providers.meteocontrol.sites import get_systems
        from negoce_ct_datamanagement.providers.meteocontrol.measurements import call_bulk_measurements_async
        from requests.exceptions import HTTPError

        systems = get_systems()
        date_to = datetime.now(timezone.utc).replace(microsecond=0)
        date_from = date_to - timedelta(hours=hours_back)

        async def process_system(system):
            key = system["key"]; name = system["name"]
            print(f"\n📡 {name} ({key}) | fenêtre: {hours_back}h")
            try:
                data = await call_bulk_measurements_async(
                    system_key=key,
                    date_from=date_from,
                    date_to=date_to,
                    resolution="fifteen-minutes",
                    include_interval=0
                )

                latest_by_inv = {}
                inv_data = (data or {}).get("inverters") or {}
                for ts, meters in inv_data.items():
                    for inv_id, measures in (meters or {}).items():
                        val = (measures or {}).get("E_INT")
                        if val not in (None, 0):
                            if inv_id not in latest_by_inv or ts > latest_by_inv[inv_id]:
                                latest_by_inv[inv_id] = ts

                if not latest_by_inv:
                    print("⚠️ Aucune mesure E_INT non-nulle sur la fenêtre."); return

                df = pd.DataFrame(
                    [{"inverter_id": inv, "last_timestamp": ts} for inv, ts in latest_by_inv.items()]
                ).sort_values("last_timestamp", ascending=False)

                print(f"🔝 TOP {per_system_top} onduleurs les plus frais :")
                print(df.head(per_system_top).to_string(index=False))

            except HTTPError as e:
                code = getattr(e.response, "status_code", "?")
                print(f"❌ {name} ({key}) HTTP {code}")
            except Exception as e:
                print(f"❌ {name} ({key}) {e}")

        await asyncio.gather(*(process_system(s) for s in systems))

    finally:
        # Affiche TOUJOURS le compteur, même en cas d'erreur/429
        print_http_counters(counters, title="📡 (inverters latest E_INT) Compteur de requêtes HTTP")
        restore()

TZ_LOCAL = "Europe/Zurich"

def compare_station_vs_inverters(
    station: pd.Series,
    inverters: Dict[str, pd.Series],
    *,
    value_label: str = "E_INT",     # ex: énergie de l’intervalle (kWh)
    freq: str = "15T",              # 15 minutes (adapter si besoin)
    tz_station: Optional[str] = None,   # None = déjà tz-aware; sinon ex "UTC"
    tz_inverters: Optional[str] = None, # ex "Europe/Zurich" si timestamps +02:00
    tolerance: str = "2min"         # marge pour le matching de timestamps
) -> Tuple[pd.Timestamp, float, float, float, float]:
    """
    Retourne (ts_utc, station_val, sum_inverters, diff_abs, diff_pct)
    et imprime un petit rapport.

    Paramètres attendus:
      - station, inverters: Series indexées en datetime, valeurs numériques (kWh/intervalle ou W instantané).
      - freq: fréquence cible pour l’alignement (ex. '15T').
      - tz_*: renseigner si les index ne sont PAS localisés (naïfs). Si déjà tz-aware avec offset, on n’y touche pas.
    """

    def _prep(s: pd.Series, tz_hint: Optional[str]) -> pd.Series:
        s = s.sort_index()
        # Localise ou confirme la timezone
        if s.index.tz is None:
            if tz_hint is None:
                raise ValueError("Index naïf sans tz_hint fourni.")
            s.index = s.index.tz_localize(tz_hint)
        # Normalise en UTC
        s = s.tz_convert("UTC")
        # Aligne sur la grille freq (sans agréger si déjà par pas régulier)
        s = (s.resample(freq).sum() if s.index.freq is None else s)
        return s

    st = _prep(station, tz_station)

    inv_list = []
    for name, ser in inverters.items():
        inv_list.append(_prep(ser, tz_inverters).rename(name))

    if not inv_list:
        raise ValueError("Aucun onduleur fourni.")

    inv_df = pd.concat(inv_list, axis=1)
    # On garde uniquement les timestamps présents côté station (join='inner' après alignement)
    df = pd.concat([st.rename(value_label), inv_df], axis=1, join="inner")

    # Dernier timestamp commun avec au moins une donnée station + onduleurs
    # (dropna pour station; pour onduleurs on autorise des NaN puis on somme)
    common = df.dropna(subset=[value_label])
    if common.empty:
        raise ValueError("Pas de pas de temps commun entre station et onduleurs.")
    ts = common.index[-1]

    # Pour gérer de légers décalages horloge, on permet un voisinage +/- tolerance
    window = df.loc[ts - pd.Timedelta(tolerance): ts + pd.Timedelta(tolerance)]
    if window.empty:
        # fallback strict au timestamp exact
        window = df.loc[[ts]]

    # On agrège sur la/les lignes trouvées (le plus souvent une seule)
    station_val = window[value_label].sum()
    sum_inverters = window.drop(columns=[value_label]).sum(axis=1, skipna=True).sum()

    diff_abs = station_val - sum_inverters
    diff_pct = (diff_abs / station_val * 100.0) if station_val != 0 else float("nan")

    ts_utc = ts.tz_convert("UTC")
    ts_local = ts.tz_convert(TZ_LOCAL)

    print(f"🕒 Timestamp (UTC):   {ts_utc.isoformat()}")
    print(f"🕒 Timestamp (local): {ts_local.isoformat()}  [{TZ_LOCAL}]")
    print(f"🏷️  Métrique: {value_label}  | Pas: {freq}")
    print(f"📡 Station:   {station_val:.6f}")
    print(f"🔌 Onduleurs: {sum_inverters:.6f}")
    print(f"Δ Absolu:     {diff_abs:.6f}")
    print(f"Δ Relatif:    {diff_pct:.3f}%")

    return ts_utc, station_val, sum_inverters, diff_abs, diff_pct

async def run_one_station(
    system_key: str,
    *,
    print_full: bool = True,
    day_start_local: str = "06:00",      # fenêtre “heures de jour” (heure locale)
    day_end_local: str = "20:00",
    pct_threshold: float = 5.0,          # seuil d’écart relatif (%)
    abs_threshold_kwh: float = 0.05      # seuil d’écart absolu (kWh)
):
    """
    Récupère station + onduleurs sur 24h, compare:
      - dernier pas commun (comme avant)
      - TOUS les pas de 15 min de la fenêtre
    Signale les écarts > seuils et imprime un récap global + heures de jour.
    """
    import requests, httpx
    import pandas as pd
    import numpy as np
    from zoneinfo import ZoneInfo

    # --- Compteurs ---
    counters = {
        "total": 0,
        "requests_get": 0, "requests_post": 0,
        "httpx_get": 0,    "httpx_post": 0,
        "login_calls": 0,
        "status_2xx": 0,
        "status_4xx": 0, "status_429": 0,
        "status_5xx": 0,
    }

    # --- Sauvegarde des méthodes d'origine ---
    _orig_requests_get = requests.get
    _orig_requests_post = requests.post
    _orig_httpx_get = httpx.AsyncClient.get
    _orig_httpx_post = httpx.AsyncClient.post

    def _extract_url(args, kwargs):
        return (kwargs.get("url")
                if isinstance(kwargs, dict) and "url" in kwargs
                else (args[0] if args else None))

    # --- Wrappers requests (sync) ---
    def _requests_get_wrapper(*args, **kwargs):
        counters["total"] += 1
        counters["requests_get"] += 1
        resp = _orig_requests_get(*args, **kwargs)
        sc = getattr(resp, "status_code", None)
        if sc is not None:
            if 200 <= sc < 300: counters["status_2xx"] += 1
            elif 400 <= sc < 500:
                counters["status_4xx"] += 1
                if sc == 429: counters["status_429"] += 1
            elif 500 <= sc < 600: counters["status_5xx"] += 1
        return resp

    def _requests_post_wrapper(*args, **kwargs):
        url = _extract_url(args, kwargs)
        counters["total"] += 1
        counters["requests_post"] += 1
        if url and str(url).endswith("/login"):
            counters["login_calls"] += 1
        resp = _orig_requests_post(*args, **kwargs)
        sc = getattr(resp, "status_code", None)
        if sc is not None:
            if 200 <= sc < 300: counters["status_2xx"] += 1
            elif 400 <= sc < 500:
                counters["status_4xx"] += 1
                if sc == 429: counters["status_429"] += 1
            elif 500 <= sc < 600: counters["status_5xx"] += 1
        return resp

    # --- Wrappers httpx (async) ---
    async def _httpx_get_wrapper(self, *args, **kwargs):
        counters["total"] += 1
        counters["httpx_get"] += 1
        resp = await _orig_httpx_get(self, *args, **kwargs)
        sc = getattr(resp, "status_code", None)
        if sc is not None:
            if 200 <= sc < 300: counters["status_2xx"] += 1
            elif 400 <= sc < 500:
                counters["status_4xx"] += 1
                if sc == 429: counters["status_429"] += 1
            elif 500 <= sc < 600: counters["status_5xx"] += 1
        return resp

    async def _httpx_post_wrapper(self, *args, **kwargs):
        url = _extract_url(args, kwargs)
        counters["total"] += 1
        counters["httpx_post"] += 1
        if url and str(url).endswith("/login"):
            counters["login_calls"] += 1
        resp = await _orig_httpx_post(self, *args, **kwargs)
        sc = getattr(resp, "status_code", None)
        if sc is not None:
            if 200 <= sc < 300: counters["status_2xx"] += 1
            elif 400 <= sc < 500:
                counters["status_4xx"] += 1
                if sc == 429: counters["status_429"] += 1
            elif 500 <= sc < 600: counters["status_5xx"] += 1
        return resp

    # --- Patch global ---
    requests.get = _requests_get_wrapper
    requests.post = _requests_post_wrapper
    httpx.AsyncClient.get = _httpx_get_wrapper
    httpx.AsyncClient.post = _httpx_post_wrapper

    try:
        from negoce_ct_datamanagement.providers.meteocontrol._config import get_api_async
        from negoce_ct_datamanagement.providers.meteocontrol.measurements import call_bulk_measurements_async
        from urllib.parse import quote_plus

        # Fenêtre 24h
        date_to = datetime.now().replace(
            hour=23, minute=45, second=0, microsecond=0
        )
        date_from = date_to - timedelta(hours=24)

        # --- 1) Station (E_Z_EVU cumulatif) ---
        api = get_api_async()
        station_resp = await api.send_request(
            "systems/{}/basics/abbreviations/E_Z_EVU/measurements"
            "?from={}&to={}&resolution=fifteen-minutes".format(
                system_key,
                quote_plus(date_from.isoformat()),
                quote_plus(date_to.isoformat()),
            )
        )
        points = (station_resp or {}).get("data", {}).get("E_Z_EVU", [])
        st_cum = pd.Series({
            pd.to_datetime(p["timestamp"], utc=True): p.get("value")
            for p in points
        }).sort_index()
        st_cum.name = "E_Z_EVU_cum"

        # -> Energie d'intervalle (kWh/15min) via diff
        st_interval = st_cum.diff()
        # Nettoyage: valeurs négatives (reset compteur, rollback, bruit) -> NaN
        st_interval = st_interval.where(st_interval >= 0)
        # Option: petit bruit négatif toléré
        # eps = 1e-6; st_interval = st_interval.where(st_interval >= -eps).clip(lower=0)

        # --- 2) Onduleurs (E_INT) ---
        inv_resp = await call_bulk_measurements_async(
            system_key=system_key,
            date_from=date_from,
            date_to=date_to,
            resolution="fifteen-minutes",
        )
        inverters_dict = {}
        for ts, devs in (inv_resp.get("inverters", {}) or {}).items():
            ts_dt = pd.to_datetime(ts, utc=True, errors="coerce")
            for inv_id, measures in (devs or {}).items():
                val = measures.get("E_INT")
                inverters_dict.setdefault(inv_id, {})[ts_dt] = val

        inv_series_dict = {k: pd.Series(v).sort_index() for k, v in inverters_dict.items()}
        inverter_count = len(inv_series_dict)
        print(f"\n🔌 Nombre d'onduleurs détectés : {inverter_count}")

        # Affichage exhaustif (station + onduleurs)
        if print_full:
            print(f"\n📡 Station {system_key} — E_Z_EVU cumulatif (UTC): {st_cum.shape[0]} points")
            with pd.option_context("display.max_rows", None, "display.width", 200):
                print(st_cum.to_string())
            print(f"\n📡 Station {system_key} — E_Z_EVU intervalle (UTC): {st_interval.shape[0]} points")
            with pd.option_context("display.max_rows", None, "display.width", 200):
                print(st_interval.to_string())

            for inv_id, ser in sorted(inv_series_dict.items()):
                ser.name = f"inverter_{inv_id}_E_INT"
                non_null = ser.dropna().shape[0]
                print(f"\n— Onduleur {inv_id}: {ser.shape[0]} points (non-nuls: {non_null})")
                with pd.option_context("display.max_rows", None, "display.width", 200):
                    print(ser.to_string())

        # --- 3) Alignement sur grille 15min (UTC), somme onduleurs ---
        # (si trous, on ne remplit PAS; on garde NaN pour signaler)
        st_15 = st_interval.resample("15min").sum()
        inv_df = pd.DataFrame(inv_series_dict).resample("15min").sum(min_count=1)
        sum_inv = inv_df.sum(axis=1, skipna=True)
        sum_inv.name = "sum_inverters"

        # DF commun
        df = pd.concat([st_cum.rename("station_cumul"), sum_inv], axis=1, join="inner").sort_index()

        # Différences absolues
        df["diff_abs"] = df["station_cumul"] - df["sum_inverters"]

        # % relatif basé sur station_cumul ; évite division par 0 -> NaN
        df["diff_pct"] = np.where(
            df["station_cumul"].abs() > 0,
            df["diff_abs"] / df["station_cumul"] * 100.0,
            np.nan
        )

        # --- 4) Détection d'écarts (toute la fenêtre) ---
        mask_large = (
            df["diff_abs"].abs() > abs_threshold_kwh
        ) & (
            df["diff_pct"].abs() > pct_threshold
        )
        n_large = int(mask_large.sum())

        print("\n🧾 Récap sur 24h (tous les pas 15min):")
        print(f"- Points communs: {df.shape[0]}")
        print(f"- Écarts > {abs_threshold_kwh:.2f} kWh ET > {pct_threshold:.1f}% : {n_large}")

        if print_full and not df.empty:
            with pd.option_context("display.max_rows", None, "display.width", 220, "display.float_format", lambda x: f"{x:,.6f}"):
                print("\n📋 Tableau complet (UTC):")
                print(df.to_string())

        # Stats globales utiles
        if not df.empty:
            mae = df["diff_abs"].abs().mean(skipna=True)
            max_abs = df["diff_abs"].abs().max(skipna=True)
            max_row = df["diff_abs"].abs().idxmax() if not np.isnan(max_abs) else None
            print(f"\n📊 Stats 24h:")
            print(f"- MAE (kWh): {mae:.6f}")
            print(f"- Max |Δ| (kWh): {max_abs:.6f} @ {max_row}")

        # --- 5) Focus “heures de jour” (local) ---
        if not df.empty:
            tz_local = ZoneInfo("Europe/Zurich")
            dfl = df.copy()
            dfl.index = dfl.index.tz_convert(tz_local)

            # Fenêtre locale 06:00–20:00
            dfl_day = dfl.between_time(day_start_local, day_end_local)
            mask_large_day = (
                dfl_day["diff_abs"].abs() > abs_threshold_kwh
            ) & (
                dfl_day["diff_pct"].abs() > pct_threshold
            )
            n_large_day = int(mask_large_day.sum())

            print(f"\n🌞 Heures de jour [{day_start_local}-{day_end_local} {tz_local.key}] :")
            print(f"- Points: {dfl_day.shape[0]}")
            print(f"- Écarts > {abs_threshold_kwh:.2f} kWh ET > {pct_threshold:.1f}% : {n_large_day}")

            if print_full and not dfl_day.empty:
                with pd.option_context("display.max_rows", None, "display.width", 220, "display.float_format", lambda x: f"{x:,.6f}"):
                    print("\n📋 Tableau heures de jour (heure locale):")
                    print(dfl_day.to_string())

        # --- 6) Comparaison “dernier pas commun” (comme avant) ---
        # (réutilise ta fonction utilitaire existante)
        ts_utc, station_val, sum_inverters, diff_abs, diff_pct = compare_station_vs_inverters(
            station=st_interval,            # <-- on passe l'INTERVALLE, pas le cumul
            inverters=inv_series_dict,
            value_label="E_INT",
            freq="15min",
            tz_station="UTC",
            tz_inverters=None,
            tolerance="2min",
        )

        print("\n🧷 Rappel (dernier pas commun):")
        print({
            "timestamp_utc": ts_utc.isoformat(),
            "station_value": float(station_val) if pd.notna(station_val) else None,
            "sum_inverters": float(sum_inverters) if pd.notna(sum_inverters) else None,
            "diff_abs": float(diff_abs) if pd.notna(diff_abs) else None,
            "diff_pct": float(diff_pct) if pd.notna(diff_pct) else None,
            "inverters_count": inverter_count,
        })

        # (Option) Sauvegardes CSV si nécessaire
        # st_cum.to_csv(f"station_{system_key}_E_Z_EVU_cum_15min.csv", header=True)
        # st_interval.to_csv(f"station_{system_key}_E_Z_EVU_interval_15min.csv", header=True)
        # pd.DataFrame(inv_series_dict).to_csv(f"inverters_{system_key}_E_INT_15min.csv")
        # df.to_csv(f"compare_{system_key}_24h_15min.csv")

    finally:
        # --- Compteurs HTTP ---
        print("\n📡 Compteur de requêtes HTTP (run_one_station)")
        print(f"- Total            : {counters['total']}")
        print(f"  • requests  GET  : {counters['requests_get']}")
        print(f"  • requests  POST : {counters['requests_post']}")
        print(f"  • httpx     GET  : {counters['httpx_get']}")
        print(f"  • httpx     POST : {counters['httpx_post']}")
        print(f"  • appels /login  : {counters['login_calls']}")
        print(f"  • 2xx            : {counters['status_2xx']}")
        print(f"  • 4xx            : {counters['status_4xx']}   (429={counters['status_429']})")
        print(f"  • 5xx            : {counters['status_5xx']}")

        # --- Restore ---
        requests.get = _orig_requests_get
        requests.post = _orig_requests_post
        httpx.AsyncClient.get = _orig_httpx_get
        httpx.AsyncClient.post = _orig_httpx_post

def test_belvis_data():
    options = ReadOptions(
            precision=4,
            blocking=True,
            taskid=789
        )
    df = read_timeseries(
            timeseries_id=83692048,
            date_from=datetime(2025, 10, 3, tzinfo=timezone.utc),
            date_to=datetime(2025, 10, 6, tzinfo=timezone.utc),
            options=options
        )
    print(df)
    if isinstance(df, list):
        df = pd.DataFrame(df)

    # Parse du timestamp ISO + tri
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values("ts")

    # Optionnel : convertir en heure locale (Europe/Zurich)
    df["ts_local"] = df["ts"].dt.tz_convert("Europe/Zurich")

    # Mettre l'index temporel
    df = df.set_index("ts_local")

    # Forcer les valeurs manquantes à NaN (None -> NaN), utile pour avoir des "trous" sur le graphe
    df["v"] = pd.to_numeric(df["v"], errors="coerce")

    # (Optionnel) ne garder qu’une seule perf flag si tu veux, sinon la trace inclura tout
    # df = df[df["pf"] != "missing"]

    # Tracé
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["v"], linewidth=1.5)

    ax.set_title("Timeseries 83692048 — puissance (15 min) [heure locale]", pad=12)
    ax.set_xlabel("Heure (Europe/Zurich)")
    ax.set_ylabel("v")
    ax.grid(True, which="both", alpha=0.3)

    # Petites améliorations d’axe temps
    fig.autofmt_xdate()

    plt.tight_layout()
    backend = matplotlib.get_backend().lower()
    if "agg" in backend or "inline" in backend:
        out = Path("timeseries_83692048.png")
        plt.savefig(out, dpi=160, bbox_inches="tight")
        print(f"Graph enregistré → {out.resolve()}")
    else:
        plt.show()


def debug_rate_limits_once():
    """
    Fait un GET direct sur /session (ou /systems) avec le token actuel,
    imprime *toutes* les en-têtes reçues (même en 429).
    """
    import requests
    from negoce_ct_datamanagement.providers.meteocontrol._config import get_api
    api = get_api()
    api.ensure_token()  # s'assure d'avoir un access_token valide (login a ses propres quotas)
    url = f"{api.api_urlbase}/session"  # léger; change en /systems si tu veux
    headers = {
        "Authorization": f"Bearer {api.access_token}",
        "x-api-key": api.api_key
    }
    resp = requests.get(url, headers=headers)
    # pas de raise_for_status -> on peut inspecter même si 4xx/429
    print(f"\n🔎 Probe status: {resp.status_code}")
    print("🔎 ALL HEADERS:")
    for k, v in resp.headers.items():
        print(f"- {k}: {v}")
    print("\n🔎 Limites extraites:")
    _print_current_limits(resp)


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
    print(f"▶ total_production_timeseries_fine() | from={date_from.isoformat()} to={date_to.isoformat()} res={resolution} abbrev={abbreviation}")

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


def save_realized_sig_pv_4months() -> Dict[str, Any]:
    """
    Charge la production PV totale sur les 3 derniers mois (par jour) via
    total_production_timeseries_fine(), convertit en MW moyens (QH),
    et sauvegarde dans Belvis.

    - Gestion des 429 (retry/backoff jusqu'à 3 fois)
    - Pause de 52s toutes les 2 journées traitées (throttle)
    - Sauvegarde Belvis jour par jour
    - Retourne un petit rapport récapitulatif
    """
    stations = [
        "$SPI112_Rambossons_23_production",
        "$SPI117_Celliers_production",
        "$SPI123_Aigues_vertes_production",
        "$SPI134_Chevillarde_production",
        "$SPI135_CTN8_production",
        "$SPI138_Quarz_Up_production",
        "$SS06_Firsolar_1,2_production",
        "$SS08.1_Lignon_2_production",
        "$SS08.2_SIG_Bât_41-44_Resto_production",
        "$SS08.3_Lignon_Parking_Moto_production",
        "$SS08.4_Carport_Jura_production",
        "$SS08.5_Tours_Lignon_11_12_13_production",
        "$SS08.6_Couvert_à_vélos_production",
        "$SS12_Longirod_production",
        "$SS16_Tambourine_production",
        "$SS20_EMS_Pt-Saconnex_production",
        "$SS24_Rolex_PLO_production",
        "$SS26.1_Rolex_Chene-Bourg_CE_production",
        "$SS26.2_Rolex_Chene-Bourg_CC_production",
        "$SS28_Fondation_Pallanterie_production",
        "$SS29_Carport_Sous-Moulin_production",
        "$SS38_OBA_EC_Frontenex_production",
        "$SS40_Ci_Epeisses_production",
        "$SS46_OBA_CO_Claparède_production",
        "$SS47_OBA_CO_Vuillonnex_production",
        "$SS50_Lancy_Omnisport_production",
        "$SS52.1_Plage_Des_Eaux-Vives_Pêcheurs_production",
        "$SS52.2_Plage_Des_Eaux-Vives_Môle_Buvette_production",
        "$SS53_OBA_CO_Colombières_production",
        "$SS54_OBA_CO_Bois_Caran_production",
        "$SS56_OBA_CO_Aubépine_production",
        "$SS57_OBA_CO_Golette_production",
        "$SS59_OBA_Arsenal_Meyrin_production",
        "$SS64_Stade_de_Genève_production",
        "$SS66_Port_Francs_production",
        "$SS68_Jetée_Frontale_Nord_production",
        "$SS69_Tri-Bagage_production",
        "$SS72_OBA_CO_Voiret_production",
        "$SS73_OBA_CO_BUDE_production",
        "$SS74.1_Step Villette_production",
        "$SS74.2_Vilette_2_production",
        "$SS75_FTI_Zibay_production",
        "$SS78_Tronchet_production",
        "$SS82_Halle_Mâchefers_production",
        "$SS87_STEP_d_Aïre_production",
        "$SS88_Belle_Terre_production",
        "$SS89_STEP_Bois_De_Bay_production",
        "$SS90_OCBA_CO_Coudriers_production",
        "$SS92_Quartier_Etang_production",
        "$SS96_Parc_Des_Crêts_production",
        "$SS100_Piste_cyclable_Satigny_production",
        "$SS108_Prelco_production",
        "$SS114_Verbois_2_production",
        "$SS115_OBA_Pontet_33_production",
        "$SS125_Carouge_Val_d_Arve_production",
        "$SS130_Vernier_112_production",
        "$SS136_Hotel_logistique_ZIBAY_production"
    ]
    TZ_LOCAL = "Europe/Zurich"
    tz = ZoneInfo(TZ_LOCAL)

    now_local_midnight = pd.Timestamp.now(tz=TZ_LOCAL).normalize()
    #25 octobre 2025 debut
    start_local = pd.Timestamp(2025, 10, 26, 23, 0, 0, tz=TZ_LOCAL)
    end_local_excl = pd.Timestamp(2025, 10, 27, 21, 59, 0, tz=TZ_LOCAL)
    days_local = pd.date_range(start=start_local, end=end_local_excl, freq="D", inclusive="left")

    processed_days: List[str] = []
    errors_by_day: Dict[str, Any] = {}
    last_point_saved = None

    print(f"📆 Sauvegarde Belvis sur {len(days_local)} jours : "
          f"{start_local.date()} → {(end_local_excl - pd.Timedelta(days=1)).date()} (inclus)")

    for i, d_local in enumerate(days_local, 1):
        day_start_local = d_local.replace(hour=7, minute=0, second=0, microsecond=0)
        day_end_local   = (d_local + pd.Timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)


        start_utc = day_start_local.tz_convert("UTC")
        end_utc = day_end_local.tz_convert("UTC")
        label_day = str(day_start_local.date())

        print(f"\n➡️  [{i}/{len(days_local)}] {label_day}  (UTC: {start_utc} → {end_utc})")

        # --- Retry simple sur 429 ---
        max_retries = 3
        backoff = 15  # secondes
        attempt = 0
        s_day = None
        report_day = None

        while attempt < max_retries:
            attempt += 1
            try:
                # total_production_timeseries_fine retourne (Series, Dict)
                s_day, report_day = total_production_timeseries_fine(
                    station_names=stations,
                    date_from=start_utc.to_pydatetime(),
                    date_to=end_utc.to_pydatetime(),
                    resolution="fifteen-minutes",
                    abbreviation="E_Z_EVU",
                )
                print(f"S_day obtenu: {s_day.shape[0]} points")
                print(f"report: {report_day}")
                break
            except HTTPError as e:
                code = getattr(e.response, "status_code", None)
                print(f"❌ HTTP {code} (tentative {attempt}/{max_retries})")
                if code == 429 and attempt < max_retries:
                    wait_s = backoff * attempt
                    print(f"⏳ 429 — pause {wait_s}s puis retry…")
                    pytime.sleep(wait_s)
                    continue
                else:
                    errors_by_day[label_day] = {"http_error": str(e)}
                    break
            except Exception as ex:
                print(f"❌ Exception inattendue sur {label_day}: {ex}")
                errors_by_day[label_day] = {"exception": str(ex)}
                break

        # s_day est une pd.Series indexée par timestamp (UTC), valeurs en kWh/QH
        if s_day is None or s_day.empty:
            print("⚠️ Série vide — aucune sauvegarde Belvis pour ce jour.")
            if report_day:
                errors_by_day[label_day] = {"report": report_day}
            if i % 2 == 0 and i != len(days_local):
                pytime.sleep(32)
            continue

        # --- Conversion kWh → MW moyens sur 15 min: ×4 / 1000 ---
        # Option: si Belvis attend l'heure locale, remplacer .index.tz_convert("Europe/Zurich")
        df_to_save = pd.DataFrame({
            "datetime": s_day.index,  # tz-aware
            "Meteocontrol_production_mesurée.MW.QH.O": (s_day * 4.0 / 1000.0).astype(float),
        }).reset_index(drop=True)

        try:
            save_meteocontrol_production(df_to_save)
            processed_days.append(label_day)

            clean = df_to_save.dropna(subset=["Meteocontrol_production_mesurée.MW.QH.O"])
            if not clean.empty:
                last_point_saved = clean.iloc[-1]["datetime"]
        except Exception as ex:
            print(f"❌ Erreur sauvegarde Belvis {label_day}: {ex}")
            errors_by_day[label_day] = {"belvis_error": str(ex), "report": report_day}

        # throttle toutes les 2 journées
        if i % 2 == 0 and i != len(days_local):
            print("⏳ Pause de 32 secondes (throttle)…")
            pytime.sleep(32)

    print("\n✅ Sauvegarde terminée.")
    return {
        "days_processed": processed_days,
        "errors": errors_by_day,
        "last_point_saved": last_point_saved,
        "period_local": {
            "from_inclusive": str(start_local.date()),
            "to_inclusive": str((end_local_excl - pd.Timedelta(days=1)).date()),
        },
    }


if __name__ == "__main__":
    save_realized_sig_pv_4months()
    #asyncio.run(test_speed_fetch_production_for_all_systems())
    #debug_rate_limits_once()
    # test_forecast_specific()
    # asyncio.run(test_collect_nominal_powers_over_one_month())
    # compare_speed_fetch_production()
    # asyncio.run(test_collect_nominal_powers())
    # specific_energy_value_consistency()
    # specific_energy_minimal_date()
    # specific_energy_minimal_date_superposed()
    # test_satellite_irradiance()
    # test_single_satellite_irradiance()
    # specific_energy_compare_all_systems()
    
    #asyncio.run(test_latest_realized_per_system_async(top_n=10))
    # asyncio.run(test_latest_realized_per_inverter_async(hours_back=24, per_system_top=10))
    
    # asyncio.run(run_one_station("VI8PR"))
    # asyncio.run(run_one_station("33GTN"))

    # test_belvis_data()
