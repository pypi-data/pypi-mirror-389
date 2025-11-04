from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Optional, Iterable, Tuple, Any

from zoneinfo import ZoneInfo

from negoce_ct_datamanagement.models.timeseries import PointIn, Series
from negoce_ct_datamanagement.repo.timeseries import TimeseriesRepo


DEFAULT_THRESHOLD = 200_000   
DEFAULT_CHUNK_SIZE = 10_000  
DEFAULT_ASSUME_TZ = "Europe/Zurich"

@dataclass(frozen=True)
class RefInfo:
    series_id: Optional[int]
    name: str
    provider: Optional[str]
    domain: Optional[str]
    type: Optional[str]
    area_code: Optional[str]
    description: Optional[str]
    issue_time: Optional[datetime] 


# -------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------

TupleRecord = Tuple[str, str, int, str, Any, Any, Any, Iterable]  # (frequency, time_zone, id, name, issue_date, created, modified, points)

def _map_tuple_records_to_items(
    records: list[TupleRecord],
    assume_tz: str
) -> list[dict]:
    """
    Transforme les tuples plats en dicts homogènes pour le pipeline existant.
    `modified` est conservé dans `_force_issue_time` pour écraser ensuite l'issue_time.
    """
    mapped: list[dict] = []
    for rec in records:
        if not isinstance(rec, tuple) or len(rec) < 8:
            continue
        frequency, time_zone, id_, name, issue_date, created, modified, points = rec
        mapped.append(
            {
                "frequency": frequency,
                "time_zone": time_zone or assume_tz,
                "id": id_,
                "name": name,
                "issue_date": issue_date,   # conservé à titre informatif si _make_ref l'utilise
                "created": created,
                "modified": modified,
                "points": points,
                "_force_issue_time": modified,  # 👈 indicateur pour forcer l'issue_time
            }
        )
    return mapped

def _looks_like_point_dict(d: dict) -> bool:
    if not isinstance(d, dict):
        return False
    keys = {str(k).lower() for k in d.keys()}
    has_ts = bool({"ts", "timestamp", "time", "datetime", "target_time"} & keys)
    has_v  = bool({"v", "value"} & keys)
    return has_ts and has_v

def _coerce_items(payload: list[dict] | dict | list[tuple], assume_tz: str) -> list[dict]:
    # Normalise payload en liste de dicts (supporte dict, liste de dicts, et liste de tuples).
    if isinstance(payload, list):
        if payload and isinstance(payload[0], tuple):
            return _map_tuple_records_to_items(payload, assume_tz=assume_tz)
        if payload and isinstance(payload[0], dict) and _looks_like_point_dict(payload[0]):
            # 👇 wrappe toute la liste de points dans un seul item
            return [{"points": payload}]
        return payload
    else:
        return [payload]

def _to_datetime_utc(x: Any, *, assume_tz: str) -> Optional[datetime]:
    """
    Convertit x en datetime UTC.
    - int/float : epoch en secondes ou millisecondes (heuristique)
    - str       : ISO-8601 (via _parse_iso_to_utc) ou entier epoch
    """
    if x is None:
        return None
    # Numérique -> epoch
    if isinstance(x, (int, float)):
        # Heuristique: >= 10^12 => millisecondes; sinon secondes
        sec = float(x) / (1000.0 if abs(float(x)) >= 1_000_000_000_000 else 1.0)
        return datetime.fromtimestamp(sec, tz=timezone.utc)
    # Str -> ISO ou entier epoch
    if isinstance(x, str):
        s = x.strip()
        if s.isdigit():
            return _to_datetime_utc(int(s), assume_tz=assume_tz)
        try:
            return _parse_iso_to_utc(s, assume_tz)
        except Exception:
            return None
    return None

def _find_col_indices(columns: list[str]) -> tuple[Optional[int], Optional[int]]:
    """
    Détecte les indices des colonnes timestamp et value dans une liste de noms.
    - ts: 'ts', 'timestamp', 'time', 'datetime', 'target_time'
    - v:  'v', 'value'
    Retourne (idx_ts, idx_v).
    """
    if not columns:
        return (None, None)
    cols = [str(c).strip().lower() for c in columns]
    def find(any_of: set[str]) -> Optional[int]:
        for i, c in enumerate(cols):
            if c in any_of:
                return i
        return None

    idx_ts = find({"ts", "timestamp", "time", "datetime", "target_time"})
    idx_v  = find({"v", "value"})
    return (idx_ts, idx_v)


def _parse_iso_to_utc(s: str, assume_tz: str) -> datetime:
    """
    Parse ISO-8601 en UTC.
    - Supporte 'Z' => +00:00
    - Si pas de timezone dans la string, on suppose `assume_tz` (ex: Europe/Zurich)
    """
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(assume_tz))
    return dt.astimezone(timezone.utc)


def _is_finite_number(x: Any) -> bool:
    try:
        f = float(x)
    except (TypeError, ValueError):
        return False
    return f == f and f not in (float("inf"), float("-inf"))  # NaN/Inf guards


def _dedupe_keep_last(items: Iterable[tuple[datetime, float]]) -> list[tuple[datetime, float]]:
    """
    Déduplique sur target_time (UTC), en gardant la dernière valeur rencontrée.
    (Stable pour notre parcours séquentiel.)
    """
    last: dict[datetime, float] = {}
    for t, v in items:
        last[t] = v
    return sorted(last.items(), key=lambda kv: kv[0])


def _make_ref(item: dict, *, assume_tz: str, use_modified_as_issue_time: bool) -> RefInfo:
    ref = item.get("ref") or {}
    tl_id = item.get("id")
    tl_name = item.get("name")
    tl_modified = item.get("modified")
    # Priorité à ref.* s’il existe; sinon top-level
    series_id = ref.get("id", tl_id)
    name = (ref.get("name") or tl_name or "") 
    provider = ref.get("provider")
    domain = ref.get("domain")
    typ = ref.get("type")
    area = ref.get("area")
    description = ref.get("description")

    issue_time = None
    if use_modified_as_issue_time and (ref.get("modified") or tl_modified):
        issue_time = _parse_iso_to_utc(ref.get("modified") or tl_modified, assume_tz)

    return RefInfo(
        series_id=series_id if isinstance(series_id, int) else None,
        name=name,
        provider=provider,
        domain=domain,
        type=typ,
        area_code=area,
        description=description,
        issue_time=issue_time,
    )



# -------------------------------------------------------------------
# Ingestion
# -------------------------------------------------------------------

async def _write_points_chunked(
    repo: TimeseriesRepo,
    sid: int,
    points: list[PointIn],
    chunk_size: int,
) -> int:
    total = 0
    if len(points) <= chunk_size:
        total += await repo.write_points(sid, points)
        return total
    for i in range(0, len(points), chunk_size):
        total += await repo.write_points(sid, points[i:i + chunk_size])
    return total


async def _copy_points_fixed_issue_time(repo, sid, rows, issue_time):
    def fmt(dt):  # RFC3339 UTC
        return dt.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with_issue = issue_time is not None
    if with_issue:
        iss = fmt(issue_time)
        lines = [f"{sid},{fmt(t)},{float(v)},{iss}" for t, v in rows]
        cols = "(series_id, target_time, value, issue_time)"
        create_tmp = """
            CREATE TEMP TABLE tmp_points (
              series_id   int NOT NULL,
              target_time timestamptz NOT NULL,
              value       double precision NOT NULL,
              issue_time  timestamptz NOT NULL
            ) ON COMMIT DROP;
        """
        insert_merge = """
            INSERT INTO points (series_id, target_time, value, issue_time)
            SELECT series_id, target_time, value, issue_time FROM tmp_points
            ON CONFLICT (series_id, target_time, value)
            DO UPDATE SET issue_time = EXCLUDED.issue_time
            WHERE EXCLUDED.issue_time > points.issue_time;
        """
    else:
        lines = [f"{sid},{fmt(t)},{float(v)}" for t, v in rows]
        cols = "(series_id, target_time, value)"
        create_tmp = """
            CREATE TEMP TABLE tmp_points (
              series_id   int NOT NULL,
              target_time timestamptz NOT NULL,
              value       double precision NOT NULL
            ) ON COMMIT DROP;
        """
        insert_merge = """
            INSERT INTO points (series_id, target_time, value, issue_time)
            SELECT series_id, target_time, value, now() FROM tmp_points
            ON CONFLICT (series_id, target_time, value)
            DO UPDATE SET issue_time = EXCLUDED.issue_time
            WHERE EXCLUDED.issue_time > points.issue_time;
        """

    data = ("\n".join(lines) + "\n").encode("utf-8")

    await repo.pool.open()
    async with repo.pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(create_tmp)
            async with cur.copy(f"COPY tmp_points {cols} FROM STDIN WITH (FORMAT csv)") as cp:
                await cp.write(data)
            await cur.execute(insert_merge)
            inserted = cur.rowcount or 0
    return inserted


async def ingest_points_json(
    *,
    payload: list[dict] | dict | list[tuple],
    assume_tz: str = DEFAULT_ASSUME_TZ,
    use_modified_as_issue_time: bool = True,
    threshold: int = DEFAULT_THRESHOLD,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    repo: Optional[TimeseriesRepo] = None,
    series_id: Optional[int] = None, 
) -> dict:
    _repo = repo or TimeseriesRepo()
    series_out: list[dict] = []
    total_points = 0
    inserted_total = 0
    method_counts = {"COPY": 0, "INSERT": 0, "NONE": 0, "NOCHANGE": 0, "ERROR": 0}
    details: list[dict] = []
    items = _coerce_items(payload, assume_tz=assume_tz)
    if items and isinstance(items[0], dict) and _looks_like_point_dict(items[0]) and all(isinstance(x, dict) for x in items):
        items = [{"points": items}]

    for item in items or []:
        item_tz = item.get("time_zone") or assume_tz
        ref = _make_ref(
            item,
            assume_tz=item_tz,
            use_modified_as_issue_time=use_modified_as_issue_time,
        )

        # --- Résolution de l'ID (priorité: ref.series_id > item.series_id > param) ---
        item_series_id = item.get("series_id")
        chosen_sid = ref.series_id if isinstance(ref.series_id, int) else None
        if chosen_sid is None and isinstance(item_series_id, int):
            chosen_sid = item_series_id
        if chosen_sid is None and isinstance(series_id, int):
            chosen_sid = series_id
        if chosen_sid is not None and chosen_sid != ref.series_id:
            ref = replace(ref, series_id=chosen_sid)

        # --- Forçage issue_time pour format tuple record ---
        if "_force_issue_time" in item:
            forced = _to_datetime_utc(item["_force_issue_time"], assume_tz=item_tz)
            if forced is not None:
                ref = replace(ref, issue_time=forced)

        # --- Décider si on "assure" la série ou si on bypasse ---
        has_meta = bool((ref.name and ref.name.strip()) or ref.provider or ref.domain or ref.type or ref.area_code or ref.description)
        sid: int

        if ref.series_id is not None and not has_meta:
            # Mode "ID connu, pas de meta" : ne pas créer/assurer la série
            sid = ref.series_id
            # (Optionnel) tu peux vérifier l'existence via le repo si tu as une méthode dédiée.
            series_out.append({"name": ref.name or "", "id": sid})
        else:
            # Soit pas d'ID, soit on a des meta -> on laisse ensure_series décider (SELECT/UPSERT/INSERT)
            series: Series = await _repo.ensure_series(
                series_id=ref.series_id,
                name=ref.name,
                provider_name=ref.provider,
                area_code=ref.area_code,
                domain_name=ref.domain,
                type_name=ref.type,
                unit_name=None,
                description=ref.description,
            )
            sid = series.id
            series_out.append({"name": series.name, "id": series.id})

        # --- Extraction/normalisation des points (inchangé) ---
        raw_points = item.get("points") or item.get("data") or []
        columns = item.get("columns") or item.get("cols")

        cleaned: list[tuple[datetime, float]] = []
        item_tz = item.get("time_zone") or assume_tz

        if columns and isinstance(raw_points, list) and raw_points and isinstance(raw_points[0], (list, tuple)):
            idx_ts, idx_v = _find_col_indices(columns)
            if idx_ts is not None and idx_v is not None:
                for row in raw_points:
                    if not (isinstance(row, (list, tuple)) and len(row) > max(idx_ts, idx_v)):
                        continue
                    dt_raw = row[idx_ts]
                    val = row[idx_v]
                    if not _is_finite_number(val):
                        continue
                    t_utc = _to_datetime_utc(dt_raw, assume_tz=item_tz)
                    if t_utc is None:
                        continue
                    cleaned.append((t_utc, float(val)))

        if not cleaned:
            for p in raw_points:
                dt_raw = None
                val = None
                if isinstance(p, dict):
                    dt_raw = p.get("datetime") or p.get("target_time")
                    val = p.get("value")
                    if dt_raw is None and val is None:
                        ts_key = next((k for k in p.keys() if str(k).lower() in {"ts", "timestamp", "time", "datetime", "target_time"}), None)
                        v_key  = next((k for k in p.keys() if str(k).lower() in {"v", "value"}), None)
                        if ts_key and v_key:
                            dt_raw = p.get(ts_key)
                            val = p.get(v_key)
                elif isinstance(p, (list, tuple)):
                    if len(p) >= 2:
                        if not columns:
                            dt_raw, val = p[0], p[1]
                            if len(p) >= 3 and _to_datetime_utc(p[1], assume_tz=item_tz) is not None and _is_finite_number(p[2]):
                                dt_raw, val = p[1], p[2]
                if _is_finite_number(val):
                    t_utc = _to_datetime_utc(dt_raw, assume_tz=item_tz)
                    if t_utc is not None:
                        cleaned.append((t_utc, float(val)))

        rows = _dedupe_keep_last(cleaned)
        n = len(rows)
        total_points += n
        detail = {
            "name": ref.name,
            "series_id": None,  # on mettra sid après résolution
            "attempted_points": n,
            "method": None,
            "affected_rows": 0,
            "status": "SKIPPED" if n == 0 else "PENDING",
            "error": None,
        }
        if n == 0:
            method_counts["NONE"] += 1
            details.append(detail)
            continue

        try:
            if n > threshold:
                inserted = await _copy_points_fixed_issue_time(_repo, sid, rows, ref.issue_time)
                detail["method"] = "COPY"
                method_counts["COPY"] += 1
            else:
                pts = [PointIn(target_time=t, value=v, issue_time=ref.issue_time) for t, v in rows]
                inserted = await _write_points_chunked(_repo, sid, pts, chunk_size)
                detail["method"] = "INSERT"
                method_counts["INSERT"] += 1

            inserted_total += (inserted or 0)
            detail["affected_rows"] = int(inserted or 0)

            if detail["affected_rows"] == 0:
                # n>0 mais aucune ligne affectée (doublons / issue_time pas plus récent / etc.)
                detail["status"] = "NOCHANGE"
                method_counts["NOCHANGE"] += 1
            else:
                detail["status"] = "OK"

        except Exception as e:
            detail["status"] = "ERROR"
            detail["error"] = f"{type(e).__name__}: {e}"
            method_counts["ERROR"] += 1

        details.append(detail)

    detail["series_id"] = sid
    return {
        "series": series_out,
        "total_points": total_points,
        "inserted": inserted_total,
        "method_counts": method_counts,
        "details": details,
    }