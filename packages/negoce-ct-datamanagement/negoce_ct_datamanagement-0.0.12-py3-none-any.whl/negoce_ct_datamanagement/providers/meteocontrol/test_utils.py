import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus
import pandas as pd

from negoce_ct_datamanagement.providers.meteocontrol._config import get_api
from negoce_ct_datamanagement.providers.meteocontrol.sites import get_systems

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



if __name__ == "__main__":

    os.environ["ENV"] = "development"
    env_path = Path(__file__).parents[3] / f".env.{os.getenv('ENV')}"
    load_dotenv(env_path)
    print(f"[ENV] Loaded environment from: {env_path}")
    STATIONS = [
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
    
    start = datetime(2025, 10, 27, tzinfo=timezone.utc)
    end   = datetime(2025, 10, 28, tzinfo=timezone.utc)

    serie_agregee, rapport = total_production_timeseries_fine(STATIONS, start, end, resolution="fifteen-minutes")
    print("Rapport:", rapport)
    print(serie_agregee.head())      # kWh par pas de 15 min (somme de toutes les stations)
    print("Total période:", serie_agregee.sum(), "kWh")