import re
import pandas as pd
import unicodedata
from io import StringIO
from urllib.parse import urljoin

from negoce_ct_datamanagement.providers.meteosuisse._config import MeteoSwissSMNApi

# ---------- Helpers ----------
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def get_station_code(search_name="Genève-Cointrin") -> tuple[str, dict]:
    """
    Télécharge ogd-smn_meta_stations.csv et retourne le code station (3 lettres).
    """
    meta_url = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv"
    df = pd.read_csv(meta_url, sep=";", encoding="cp1252")

    target = strip_accents(search_name)
    mask = df["station_name"].map(lambda x: target in strip_accents(str(x)))
    if not mask.any():
        mask = df["station_name"].map(
            lambda x: ("cointrin" in strip_accents(str(x))) or ("genev" in strip_accents(str(x)))
        )
    row = df[mask].iloc[0]
    return str(row["station_abbr"]).strip(), row.to_dict()


def stac_list_items(api: MeteoSwissSMNApi, limit=200):
    """
    Itère sur /collections/{id}/items (pagination) et renvoie les items.
    """
    url = urljoin(api.base_stac, f"collections/{api.collection}/items")
    params = {"limit": limit}

    while True:
        data = api.send_request(f"collections/{api.collection}/items", params=params)
        for feat in data.get("features", []):
            yield feat

        next_link = None
        for l in data.get("links", []):
            if l.get("rel") == "next":
                next_link = l.get("href")
                break
        if not next_link:
            break

        url = next_link
        params = {}  


def find_station_asset(api: MeteoSwissSMNApi, station_code: str,
                       granularity: str = "t", frequency: str = "now") -> str:
    """
    Cherche dans les items STAC l'asset CSV correspondant à la station/granularité/fréquence.
    """
    pat = re.compile(fr"ogd-smn_?{station_code.lower()}_{granularity}_{frequency}\.csv$")
    for item in stac_list_items(api):
        for asset in item.get("assets", {}).values():
            href = asset.get("href", "")
            if href.endswith(".csv") and pat.search(href):
                return href
    raise RuntimeError(f"CSV introuvable pour {station_code} {granularity}_{frequency}")


def download_csv_with_etag(api: MeteoSwissSMNApi, url: str, etag_cache: dict= {}):
    """
    Récupère le CSV avec pré-condition If-None-Match comme recommandé par la doc.
    Retourne (text, new_etag) ou (None, existing_etag) si 304.
    """
    headers = {}
    if url in etag_cache:
        headers["If-None-Match"] = etag_cache[url]

    resp = api.session.get(url, headers=headers, timeout=api.timeout)
    if resp.status_code == 304:
        return None, etag_cache[url]
    resp.raise_for_status()
    new_etag = resp.headers.get("ETag")
    if new_etag:
        etag_cache[url] = new_etag
    return resp.text, new_etag


def parse_radiation_csv(text: str, radiation_param="gre000z0", n_last: int | None = None):
    df = pd.read_csv(StringIO(text), sep=";", encoding="cp1252")
    cols = [c for c in df.columns if c.lower().startswith("reference_timestamp")] + [radiation_param]
    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()

    tcol = [c for c in out.columns if c.lower().startswith("reference_timestamp")][0]
    out = out.rename(columns={tcol: "time_utc"})
    out["time_utc"] = pd.to_datetime(out["time_utc"], format="%d.%m.%Y %H:%M", utc=True, errors="coerce")
    out = out.dropna(subset=["time_utc"]).sort_values("time_utc")

    if n_last is not None:
        out = out.tail(n_last)
    return out

def format_for_belvis(df: pd.DataFrame,
                      value_col: str = "gre000z0",
                      ts_col: str = "time_utc",
                      pf_default: str = "valid",
                      ts_offset_min: int = 0) -> list[dict]:
    """
    ts_offset_min permet d'ajuster le timestamp avant envoi (ex: -10 pour séries 10min
    afin de convertir une valeur "fin de période" BelVis en "début de période")
    """
    records = []
    for _, row in df.iterrows():
        if pd.isna(row[value_col]) or pd.isna(row[ts_col]):
            continue
        ts = row[ts_col]
        if ts_offset_min:
            ts = ts + pd.Timedelta(minutes=ts_offset_min)
        records.append({
            "ts": ts.isoformat(),
            "v": float(row[value_col]),
            "pf": pf_default
        })
    return records
