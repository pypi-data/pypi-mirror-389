from __future__ import annotations

from typing import Optional, Dict, Iterable
from datetime import datetime, timezone
import io

from zoneinfo import ZoneInfo

try:
    import pandas as pd
    import numpy as np
except ImportError as e:
    raise RuntimeError(
        "Installez negoce_ct_datamanagement avec l'extra pandas (ex: pip install '... [pandas]')"
    ) from e

from negoce_ct_datamanagement.models.timeseries import Point, PointIn
from negoce_ct_datamanagement.repo.timeseries import TimeseriesRepo


# Colonnes indispensables
REQUIRED_COLS = {"series_id", "target_time", "value"}

# Paramètres par défaut
DEFAULT_THRESHOLD = 200_000  # au-delà on bascule sur COPY
DEFAULT_CHUNK_SIZE = 10_000  # INSERT en morceaux
DEFAULT_ASSUME_TZ = "Europe/Zurich"  

SWISSGRID_COL_SPECS = {
    "afrr_pos":   {"name": "CH aFRR+ covered",    "unit": "MW"},
    "afrr_neg":   {"name": "CH aFRR- covered",    "unit": "MW"},
    "nrv_pos":    {"name": "CH NRV+ (Import)",    "unit": "MW"},
    "nrv_neg":    {"name": "CH NRV- (Export)",    "unit": "MW"},
    "mfrr_sa_pos":{"name": "CH mFRR+ SA covered", "unit": "MW"},
    "mfrr_sa_neg":{"name": "CH mFRR- SA covered", "unit": "MW"},
    "mfrr_da_pos":{"name": "CH mFRR+ DA covered", "unit": "MW"},
    "mfrr_da_neg":{"name": "CH mFRR- DA covered", "unit": "MW"},
    "rr_pos":     {"name": "CH RR+ covered",      "unit": "MW"},
    "rr_neg":     {"name": "CH RR- covered",      "unit": "MW"},
    "frce_pos":   {"name": "CH FRCE+ (Import)",   "unit": "MW"},
    "frce_neg":   {"name": "CH FRCE- (Export)",   "unit": "MW"},
    "total_imbalance": {"name": "CH Total System Imbalance", "unit": "MW"},
    "prices_long": {"name": "CH AE price long",  "unit": "EUR/MWh"},
    "prices_short":{"name": "CH AE price short", "unit": "EUR/MWh"},
}

def _is_swissgrid_like_df(df: pd.DataFrame) -> bool:
    """Heuristique simple: pas de series_id mais une colonne datetime + au moins une colonne Swissgrid connue."""
    if "series_id" in df.columns:
        return False
    if "datetime" not in df.columns:
        return False
    known_cols = set(df.columns) & set(SWISSGRID_COL_SPECS.keys())
    return len(known_cols) > 0

async def _swissgrid_df_to_points_df(df: pd.DataFrame, repo: TimeseriesRepo) -> pd.DataFrame:
    """
    Transforme un DF Swissgrid (wide) -> DF normalisé (series_id, target_time, value[, issue_time]).
    - Localise/convertit target_time en UTC (Europe/Zurich par défaut).
    - Crée/assure les séries pour chaque colonne utile.
    """
    work = df.copy()

    # 1) timestamps -> UTC
    # La source est horodatée en Europe/Zurich; on s'aligne sur le même assumé que le reste du module. :contentReference[oaicite:3]{index=3}
    if not pd.api.types.is_datetime64_any_dtype(work["datetime"]):
        work["datetime"] = pd.to_datetime(work["datetime"], errors="coerce")
    # localise si naïf, convertit sinon
    assume = ZoneInfo(DEFAULT_ASSUME_TZ)
    work["datetime"] = work["datetime"].apply(
        lambda x: x.tz_localize(assume).astimezone(timezone.utc) if (pd.notna(x) and x.tzinfo is None)
        else (x.astimezone(timezone.utc) if pd.notna(x) else pd.NaT)
    )
    work = work[work["datetime"].notna()].copy()

    # 2) sélectionne colonnes Swissgrid présentes
    value_cols = [c for c in work.columns if c in SWISSGRID_COL_SPECS]
    if not value_cols:
        # rien d'utilisable
        return pd.DataFrame(columns=["series_id", "target_time", "value"])

    # 3) melt en long
    long_df = work.melt(id_vars=["datetime"], value_vars=value_cols,
                        var_name="metric", value_name="value")
    long_df = long_df[pd.to_numeric(long_df["value"], errors="coerce").notna()].copy()
    long_df["value"] = long_df["value"].astype(float)

    # 4) ensure_series pour chaque metric -> id
    # On utilise TimeseriesRepo.ensure_series exposé dans le même fichier. :contentReference[oaicite:4]{index=4}
    series_id_map: dict[str, int] = {}
    for m in sorted(long_df["metric"].unique()):
        spec = SWISSGRID_COL_SPECS[m]
        series = await repo.ensure_series(
            series_id=None,
            name=spec["name"],
            provider_name="Swissgrid",
            area_code="CH",
            domain_name="imbalance",
            type_name="actual",
            frequency_name="15m",
            unit_name=spec["unit"],
            description=f"Auto-import Swissgrid for '{m}'"
        )
        series_id_map[m] = series.id

    # 5) sortie normalisée
    out = pd.DataFrame({
        "series_id": long_df["metric"].map(series_id_map).astype(int),
        "target_time": long_df["datetime"],
        "value": long_df["value"],
    })

    # Harmonise via le nettoyeur standard (tri, dédoublon, types). :contentReference[oaicite:5]{index=5}
    return _clean_points_df(out)

# -------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------

def _ensure_utc(dt: datetime, assume_tz: str = DEFAULT_ASSUME_TZ) -> datetime:
    """Retourne un datetime timezone-aware en UTC.
    - Si naïf: on le considère dans `assume_tz` puis on convertit en UTC.
    - Si aware: on convertit en UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo(assume_tz)).astimezone(timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_utc_series(s: pd.Series, assume_tz: str = DEFAULT_ASSUME_TZ) -> pd.Series:
    """Parse une série de timestamps hétérogènes en UTC.
    - Gère 'Z' et offsets.
    - Si naïf: localise en `assume_tz` puis convertit en UTC.
    - Si déjà aware: convertit en UTC.
    - Valeurs non parseables -> NaT.
    Remarque: on utilise .apply pour supporter les colonnes mixtes (naïf + aware).
    """
    assume = ZoneInfo(assume_tz)

    def _one(x):
        if pd.isna(x):
            return pd.NaT
        # to_datetime sur scalaire
        ts = pd.to_datetime(x, errors="coerce")
        if pd.isna(ts):
            return pd.NaT
        if ts.tzinfo is None:  # naïf
            ts = ts.tz_localize(assume)
        else:                  # aware
            ts = ts.tz_convert(timezone.utc) if ts.tzinfo != timezone.utc else ts
        return ts.astimezone(timezone.utc)

    # Pandas peut rendre Timestamp/py-datetime: on applique proprement
    out = s.apply(_one)
    # Force dtype timezone-aware UTC
    return pd.to_datetime(out, utc=True, errors="coerce")


def _clean_points_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valide et normalise un DataFrame de points.
      - vérifie les colonnes requises
      - convertit target_time/issue_time en datetime UTC (naïf => DEFAULT_ASSUME_TZ)
      - force value en float fini
      - trie + dédoublonne sur (series_id, target_time, issue_time)
    """
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df = df.copy()

    # Timestamps en UTC (naïf => Europe/Zurich par défaut)
    df["target_time"] = _to_utc_series(pd.Series(df["target_time"]))
    if "issue_time" in df.columns:
        df["issue_time"] = _to_utc_series(pd.Series(df["issue_time"]))
    else:
        df["issue_time"] = pd.NaT

    # Valeurs finies
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[np.isfinite(df["value"])].copy()

    # Filtre timestamps non parseables
    df = df[df["target_time"].notna()].copy()

    # Tri & dédoublonnage
    df = (
        df.sort_values(["series_id", "target_time", "issue_time"])
          .drop_duplicates(
              subset=["series_id", "target_time", "issue_time"], keep="last"
          )
    )
    return df


def _iter_pointin_from_clean_df(df: pd.DataFrame) -> Dict[int, list[PointIn]]:
    """
    Convertit un DF nettoyé en dict {series_id: [PointIn, ...]}.
    (Ne pas appeler sur un DF non nettoyé.)
    """
    by_series: Dict[int, list[PointIn]] = {}
    for r in df.itertuples(index=False):
        sid = int(r.series_id)
        issue = (r.issue_time.to_pydatetime() if pd.notna(r.issue_time) else None)
        by_series.setdefault(sid, []).append(
            PointIn(
                target_time=r.target_time.to_pydatetime(),
                value=float(r.value),
                issue_time=issue,
            )
        )
    return by_series


def _iter_points_from_clean_df(df: pd.DataFrame) -> Iterable[Point]:
    """
    Pour compat: fabrique des `Point`.
    """
    now_utc = datetime.now(timezone.utc)
    for r in df.itertuples(index=False):
        yield Point(
            series_id=int(r.series_id),
            target_time=r.target_time.to_pydatetime(),
            value=float(r.value),
            issue_time=(r.issue_time.to_pydatetime() if pd.notna(r.issue_time) else now_utc),
        )


# -------------------------------------------------------------------
# API publique (ingest)
# -------------------------------------------------------------------

def df_to_points(df: pd.DataFrame) -> list[Point]:
    """Convertit un DF en liste de `Point` (inclut le nettoyage)."""
    df = _clean_points_df(df)
    return list(_iter_points_from_clean_df(df))


async def write_points_df(
    df: pd.DataFrame, *,  chunk_size: int = DEFAULT_CHUNK_SIZE, repo: Optional[TimeseriesRepo] = None
) -> int:
    """
    INSERT via le repo (ON CONFLICT DO NOTHING).
    Nettoie le DF en interne et insère par `series_id` en chunks.
    """
    df = _clean_points_df(df)
    n = len(df)
    if n == 0:
        return 0

    _repo = repo or TimeseriesRepo()
    total = 0
    for sid, g in df.groupby("series_id", sort=True):
        by_series = _iter_pointin_from_clean_df(g)
        points = by_series[int(sid)]
        if len(points) <= chunk_size:
            total += await _repo.write_points(series_id=int(sid), points=points)
        else:
            for start in range(0, len(points), chunk_size):
                end = min(start + chunk_size, len(points))
                total += await _repo.write_points(series_id=int(sid), points=points[start:end])
    return total


async def copy_points_df(
    df: pd.DataFrame,
    *,
    fixed_issue_time: Optional[datetime] = None,
    repo: Optional[TimeseriesRepo] = None,
) -> int:
    """
    COPY ultra-rapide depuis un DataFrame.
    - Si `fixed_issue_time` est fourni, il sera injecté pour TOUTES les lignes (naïf => DEFAULT_ASSUME_TZ).
    - Sinon, seules les 3 colonnes (series_id, target_time, value) sont copiées ;
      la colonne `issue_time` doit avoir un DEFAULT (ex: NOW()) en table.
    """
    df = _clean_points_df(df)
    if len(df) == 0:
        return 0

    _repo = repo or TimeseriesRepo()
    df = df.copy()

    # Formatage ISO UTC pour Postgres
    df["target_time"] = df["target_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    cols = ["series_id", "target_time", "value"]
    with_issue = False
    if fixed_issue_time is not None:
        with_issue = True
        fixed_issue_time = _ensure_utc(fixed_issue_time)  # ⟵ prend en compte le TZ par défaut si naïf
        df["issue_time"] = fixed_issue_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        cols.append("issue_time")

    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, columns=cols)
    data = buf.getvalue().encode()

    return await _repo.copy_points_csv(data, with_issue_time=with_issue)


async def ingest_points_df_auto(
    *,
    df: pd.DataFrame,
    fixed_issue_time: Optional[datetime] = None,
    threshold: int = DEFAULT_THRESHOLD,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    repo: Optional[TimeseriesRepo] = None,
    series_id: Optional[str] = None, 
) -> dict:
    """
    Ingestion DataFrame avec décision automatique INSERT vs COPY.
    Deux modes:
      1) DF normalisé: colonnes ['series_id', 'target_time', 'value'[, 'issue_time']]
         -> si 'series_id' manquant, il doit être passé en paramètre.
      2) DF Swissgrid 'wide': ['datetime', <colonnes Swissgrid...>] -> auto-transformation

    Args:
        df: DataFrame à ingérer.
        fixed_issue_time: datetime fixé pour toutes les lignes (optionnel).
        threshold: seuil pour choisir COPY vs INSERT.
        chunk_size: taille de batch pour INSERT.
        repo: repository de timeseries.
        series_id: identifiant de série à utiliser si la colonne est absente.

    Returns:
        {"inserted": int, "method": "INSERT"|"COPY"|"NONE",
         "rows": int, "mode": "normalized"|"swissgrid"}
    """
    _repo = repo or TimeseriesRepo()

    # 0) Détection Swissgrid
    mode = "normalized"
    if _is_swissgrid_like_df(df):
        df = await _swissgrid_df_to_points_df(df, _repo)
        mode = "swissgrid"
    else:
        df = _clean_points_df(df)

    n = len(df)
    if n == 0:
        return {"inserted": 0, "method": "NONE", "rows": 0, "mode": mode}

    # Vérifier la présence de series_id
    if "series_id" not in df.columns:
        if series_id is None:
            raise ValueError(
                "Le DataFrame ne contient pas de colonne 'series_id' "
                "et aucun 'series_id' n’a été fourni en paramètre."
            )
        df = df.copy()
        df["series_id"] = series_id

    # fixed_issue_time appliqué uniformément si fourni
    if fixed_issue_time is not None:
        df = df.copy()
        df["issue_time"] = _ensure_utc(fixed_issue_time)

    # Choix COPY vs INSERT
    if n > threshold:
        inserted = await copy_points_df(df, fixed_issue_time=fixed_issue_time, repo=_repo)
        return {"inserted": inserted, "method": "COPY", "rows": n, "mode": mode}

    inserted = await write_points_df(df, chunk_size=chunk_size, repo=_repo)
    return {"inserted": inserted, "method": "INSERT", "rows": n, "mode": mode}


# -------------------------------------------------------------------
# API publique (read -> DataFrame)
# -------------------------------------------------------------------

async def get_points_by_window_df(
    *,
    series_id: int,
    window_name: str = "all",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    tz: Optional[str] = "UTC",
    include_issue_time: bool = True,
    frequency: Optional[str] = None,          
    repo: Optional[TimeseriesRepo] = None,
) -> pd.DataFrame:
    """
    Interroge get_points_by_window et retourne un DataFrame trié.
    Colonnes: series_id, target_time, value, (issue_time?)
    frequency: 'raw' | 'hour'/'1h' | 'day'/'1d'
    """
    _repo = repo or TimeseriesRepo()
    rows = await _repo.get_points_by_window(
        series_id,
        window_name=window_name,
        start=start,
        end=end,
        frequency=frequency, 
    )

    cols = ["series_id", "target_time", "value"] + (["issue_time"] if include_issue_time else [])
    if not rows:
        return pd.DataFrame(columns=cols)

    data = {
        "series_id": [p.series_id for p in rows],
        "target_time": [p.target_time for p in rows],
        "value": [float(p.value) for p in rows],
    }
    if include_issue_time:
        data["issue_time"] = [p.issue_time for p in rows]

    df = pd.DataFrame(data)
    df["target_time"] = pd.to_datetime(df["target_time"], utc=True)
    if include_issue_time:
        df["issue_time"] = pd.to_datetime(df["issue_time"], utc=True)

    if tz and tz != "UTC":
        df["target_time"] = df["target_time"].dt.tz_convert(tz)
        if include_issue_time:
            df["issue_time"] = df["issue_time"].dt.tz_convert(tz)

    return df.sort_values("target_time").reset_index(drop=True)

async def get_points_latest_df(
    *,
    series_id: int,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    tz: Optional[str] = "UTC",
    include_issue_time: bool = True,
    repo: Optional[TimeseriesRepo] = None,
) -> pd.DataFrame:
    """
    Interroge la vue v_points_latest et retourne un DataFrame trié.
    Colonnes: series_id, target_time, value, (issue_time?)
    """
    _repo = repo or TimeseriesRepo()
    rows = await _repo.get_points_latest(series_id, start=start, end=end)

    cols = ["series_id", "target_time", "value"] + (["issue_time"] if include_issue_time else [])
    if not rows:
        return pd.DataFrame(columns=cols)

    data = {
        "series_id": [p.series_id for p in rows],
        "target_time": [p.target_time for p in rows],
        "value": [float(p.value) for p in rows],
    }
    if include_issue_time:
        data["issue_time"] = [p.issue_time for p in rows]

    df = pd.DataFrame(data)
    df["target_time"] = pd.to_datetime(df["target_time"], utc=True)
    if include_issue_time:
        df["issue_time"] = pd.to_datetime(df["issue_time"], utc=True)

    if tz and tz != "UTC":
        df["target_time"] = df["target_time"].dt.tz_convert(tz)
        if include_issue_time:
            df["issue_time"] = df["issue_time"].dt.tz_convert(tz)

    return df.sort_values("target_time").reset_index(drop=True)
