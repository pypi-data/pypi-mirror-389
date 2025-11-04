from __future__ import annotations

from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone

try:
    import pandas as pd  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError("pandas is required for pandas_adapter_hydrostatics") from exc

from negoce_ct_datamanagement.models.statics import (
    ExpectedFlowIn,
    FlowPowerConversionIn,
    SeujetEvacuationCapacityIn,
    LemanLevelIn,
)
from negoce_ct_datamanagement.repo.statics import StaticsRepo


async def bulk_upsert_expected_flows_df(df: 'pd.DataFrame', repo: Optional[StaticsRepo] = None) -> int:
    req = {"dam_id", "inflow", "expected_flow"}
    _ensure_cols(df, req)
    _repo = repo or StaticsRepo()
    rows = [
        ExpectedFlowIn(dam_id=int(r.dam_id), inflow=int(r.inflow), expected_flow=int(r.expected_flow))
        for r in df.itertuples(index=False)
    ]
    return await repo.bulk_upsert_expected_flows(rows)


async def bulk_upsert_flow_power_df(df: 'pd.DataFrame', repo: Optional[StaticsRepo] = None) -> int:
    req = {"dam_id", "flow", "group_no", "power_mw", "leman_level"}
    _ensure_cols(df, req)
    _repo = repo or StaticsRepo()
    rows = [
        FlowPowerConversionIn(
            dam_id=int(r.dam_id),
            flow=int(r.flow),
            group_no=int(r.group_no),
            power_mw=Decimal(str(r.power_mw)),
            leman_level=Decimal(str(r.leman_level)),
        )
        for r in df.itertuples(index=False)
    ]
    return await _repo.bulk_upsert_flow_power(rows)


async def bulk_upsert_seujet_capacities_df(df: 'pd.DataFrame', repo: Optional[StaticsRepo] = None) -> int:
    req = {"seujet_evacuation_flow", "arve_flow", "leman_level"}
    _ensure_cols(df, req)
    _repo = repo or StaticsRepo()
    rows = [
        SeujetEvacuationCapacityIn(
            seujet_evacuation_flow=int(r.seujet_evacuation_flow),
            arve_flow=int(r.arve_flow),
            leman_level=Decimal(str(r.leman_level)),
        )
        for r in df.itertuples(index=False)
    ]
    return await _repo.bulk_upsert_seujet_capacities(rows)


async def bulk_upsert_leman_levels_df(df: 'pd.DataFrame', repo: Optional[StaticsRepo] = None) -> int:
    req = {"leap_year", "month", "day"}
    _ensure_cols(df, req)
    _repo = repo or StaticsRepo()
    for col in [
        "min_arve_call_level", "max_arve_call_level",
        "min_regulation_domain", "max_regulation_domain",
    ]:
        if col not in df.columns:
            df[col] = None
    rows = [
        LemanLevelIn(
            leap_year=bool(r.leap_year),
            month=int(r.month),
            day=int(r.day),
            min_arve_call_level=(None if r.min_arve_call_level is None else Decimal(str(r.min_arve_call_level))),
            max_arve_call_level=(None if r.max_arve_call_level is None else Decimal(str(r.max_arve_call_level))),
            min_regulation_domain=(None if r.min_regulation_domain is None else Decimal(str(r.min_regulation_domain))),
            max_regulation_domain=(None if r.max_regulation_domain is None else Decimal(str(r.max_regulation_domain))),
        )
        for r in df.itertuples(index=False)
    ]
    return await _repo.bulk_upsert_leman_levels(rows)

async def power_table_df(
    barrage_names: list[str],
    group: int,
    flow: int | None = None,
    repo: Optional[StaticsRepo] = None
) -> 'pd.DataFrame':
    _repo = repo or StaticsRepo()
    rows = await _repo.query_power_rows(barrage_names, group, flow)
    df = pd.DataFrame(rows)
    return df if df.empty else df.astype({"debit": "float", "puissance": "float", "groupe": "int"}, errors="ignore")


async def power_dataframe_df(
    barrage_names: list[str],
    groups: list[int],
    repo: Optional[StaticsRepo] = None
) -> 'pd.DataFrame':
    _repo = repo or StaticsRepo()
    df = pd.DataFrame()
    for name in barrage_names:
        for g in groups:
            res = await power_table_df([name], g, repo=_repo)
            if not res.empty:
                df[f"{name}_{g}g"] = res.set_index("debit")["puissance"].sort_index()
    return df


async def seujet_series_df(
    group: int,
    cote_range: tuple[float, float] | None = None,
    max_debit: int = 1000,
    repo: Optional[StaticsRepo] = None
) -> 'pd.DataFrame':
    _repo = repo or StaticsRepo()
    rows = await _repo.query_seujet_rows(group, cote_range)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df[(df["debit"] >= 0) & (df["debit"] <= max_debit)].copy()
    if cote_range is not None:
        # moyenne par (debit, groupe) si un intervalle de cotes est fourni
        df = df.groupby(["debit", "groupe"], as_index=False)["puissance"].mean()
    df.index = df["debit"]
    return df.round(3)


async def seujet_mean_by_cotes_df(
    cote_windows: list[tuple[float, float]],
    repo: Optional[StaticsRepo] = None
) -> dict[tuple, 'pd.DataFrame']:
    out: dict[tuple, pd.DataFrame] = {}
    _repo = repo or StaticsRepo()
    for (cmin, cmax) in cote_windows:
        for g in (1, 2, 3):
            out[(g, cmin, cmax)] = await seujet_series_df(g, (cmin, cmax), repo=_repo)
    return out


async def seujet_evacuation_grid_df(repo: Optional[StaticsRepo] = None) -> 'pd.DataFrame':
    _repo = repo or StaticsRepo()
    rows = await _repo.list_seujet_evacuation_rows()
    return pd.DataFrame(rows)

def _ensure_cols(df: 'pd.DataFrame', req: set[str]) -> None:
    missing = req - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    

def _natural_sort_key(s: str):
    import re
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]

async def get_dummy_matrix_df(
    start,
    end,
    *,
    use_view: bool = True,
    as_int: bool = False,
    statics_repo: Optional[StaticsRepo] = None,
) -> pd.DataFrame:
    """
    Pandas-facing wrapper:
      - pulls rows via StaticsRepo
      - ensures UTC tz on target_time
      - builds skeleton if empty
      - optional int casting
      - natural column ordering
    """
    _repo = statics_repo or StaticsRepo()

    if use_view:
        rows = await _repo.fetch_dummy_matrix_view(start, end)
        df = pd.DataFrame(rows)
        if df.empty:
            cats = await _repo.fetch_categorical_names()
            s = start if isinstance(start, datetime) else datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
            e = end   if isinstance(end,   datetime) else datetime(end.year,   end.month,   end.day,   tzinfo=timezone.utc)
            df = pd.DataFrame({"target_time": pd.date_range(s, e, freq="15min", inclusive="left", tz="UTC")})
            for c in cats:
                df[c] = False
    else:
        long_rows = await _repo.fetch_dummy_matrix_long(start, end)
        if long_rows:
            df_long = pd.DataFrame(long_rows)  # columns: target_time, category
            # ensure tz-aware UTC for consistency
            df_long["target_time"] = pd.to_datetime(df_long["target_time"], utc=True)
            # pivot to wide booleans
            wide = (pd.crosstab(df_long["target_time"], df_long["category"]) > 0)
            # stable column set (include missing as False)
            cats = await _repo.fetch_categorical_names()
            wide = wide.reindex(columns=cats, fill_value=False)
            df = wide.reset_index()
        else:
            cats = await _repo.fetch_categorical_names()
            s = start if isinstance(start, datetime) else datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
            e = end   if isinstance(end,   datetime) else datetime(end.year,   end.month,   end.day,   tzinfo=timezone.utc)
            df = pd.DataFrame({"target_time": pd.date_range(s, e, freq="15min", inclusive="left", tz="UTC")})
            for c in cats:
                df[c] = False

    if not df.empty:
        # normalize to UTC *always*
        df["target_time"] = pd.to_datetime(df["target_time"], utc=True)

    if as_int and not df.empty:
        dcols = [c for c in df.columns if c != "target_time"]
        df[dcols] = df[dcols].astype("int8")

    # optional: natural sort of dummy columns
    if not df.empty:
        dcols = [c for c in df.columns if c != "target_time"]
        df = df[["target_time"] + sorted(dcols, key=_natural_sort_key)]

    return df
