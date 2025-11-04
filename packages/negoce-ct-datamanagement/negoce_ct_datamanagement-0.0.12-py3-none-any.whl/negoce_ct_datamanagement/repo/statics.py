from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional
from datetime import date
from psycopg.rows import dict_row
from datetime import datetime, timedelta, timezone, date
import pandas as pd
from typing import List, Dict

from negoce_ct_datamanagement.db_utils.connection import DbName, get_db_pool

from negoce_ct_datamanagement.models.statics import (
    Dam,
    ExpectedFlow,
    SeujetEvacuationCapacity,
    FlowPowerConversion,
    LemanLevel,
    ExpectedFlowIn,
    SeujetEvacuationCapacityIn,
    FlowPowerConversionIn,
    LemanLevelIn,
)
import pickle


class StaticsRepo:
    """Async repo for the hydro statics schema."""

    _opened = False

    def __init__(self, db: DbName = DbName.statics):
        self.pool = get_db_pool(db)

    async def ensure_open(self):
        if not self._opened:
            await self.pool.open()
            self._opened = True

    # ------------------ dams ------------------
    async def ensure_dam(self, name: str) -> int:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO dams (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (name,),
                )
                (did,) = await cur.fetchone()
                return int(did)

    async def get_dam(self, dam_id: int) -> Optional[Dam]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SELECT * FROM dams WHERE id = %s", (dam_id,))
                rec = await cur.fetchone()
                return Dam(**rec) if rec else None

    async def get_dam_by_name(self, name: str) -> Optional[Dam]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT * FROM dams WHERE name = %s ORDER BY id LIMIT 1",
                    (name,),
                )
                rec = await cur.fetchone()
                return Dam(**rec) if rec else None

    # -------------- expected_flows --------------
    async def upsert_expected_flow(self, e: ExpectedFlowIn) -> ExpectedFlow:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO expected_flows (dam_id, inflow, expected_flow)
                    VALUES (%(dam_id)s, %(inflow)s, %(expected_flow)s)
                    ON CONFLICT (dam_id, inflow) DO UPDATE SET expected_flow = EXCLUDED.expected_flow
                    RETURNING dam_id, inflow, expected_flow
                    """,
                    e.__dict__,
                )
                rec = await cur.fetchone()
                return ExpectedFlow(**rec)

    async def get_expected_flow(self, dam_id: int, inflow: int) -> Optional[ExpectedFlow]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT dam_id, inflow, expected_flow FROM expected_flows WHERE dam_id = %s AND inflow = %s",
                    (dam_id, inflow),
                )
                rec = await cur.fetchone()
                return ExpectedFlow(**rec) if rec else None

    async def bulk_upsert_expected_flows(self, rows: Iterable[ExpectedFlowIn]) -> int:
        await self.ensure_open()
        rows = list(rows)
        if not rows:
            return 0
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "CREATE TEMP TABLE _stg_expected_flows ("
                    " dam_id INT, inflow INT, expected_flow INT"
                    ") ON COMMIT DROP"
                )
                copy_sql = (
                    "COPY _stg_expected_flows (dam_id, inflow, expected_flow) "
                    "FROM STDIN"
                )
                async with cur.copy(copy_sql) as cp:
                    for r in rows:
                        await cp.write_row((r.dam_id, r.inflow, r.expected_flow))
                await cur.execute(
                    """
                    INSERT INTO expected_flows (dam_id, inflow, expected_flow)
                    SELECT dam_id, inflow, expected_flow FROM _stg_expected_flows
                    ON CONFLICT (dam_id, inflow) DO UPDATE
                        SET expected_flow = EXCLUDED.expected_flow
                    """
                )
                return cur.rowcount or 0

    # ----- seujet_evacuation_capacities -----
    async def upsert_seujet_capacity(self, s: SeujetEvacuationCapacityIn) -> SeujetEvacuationCapacity:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO seujet_evacuation_capacities (seujet_evacuation_flow, arve_flow, leman_level)
                    VALUES (%(seujet_evacuation_flow)s, %(arve_flow)s, %(leman_level)s)
                    ON CONFLICT (seujet_evacuation_flow, arve_flow, leman_level) DO NOTHING
                    RETURNING seujet_evacuation_flow, arve_flow, leman_level
                    """,
                    s.__dict__,
                )
                rec = await cur.fetchone()
                if not rec:
                    await cur.execute(
                        """
                        SELECT seujet_evacuation_flow, arve_flow, leman_level
                        FROM seujet_evacuation_capacities
                        WHERE seujet_evacuation_flow = %s AND arve_flow = %s AND leman_level = %s
                        """,
                        (s.seujet_evacuation_flow, s.arve_flow, s.leman_level),
                    )
                    rec = await cur.fetchone()
                return SeujetEvacuationCapacity(**rec)

    async def bulk_upsert_seujet_capacities(self, rows: Iterable[SeujetEvacuationCapacityIn]) -> int:
        await self.ensure_open()
        rows = list(rows)
        if not rows:
            return 0
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "CREATE TEMP TABLE _stg_seujet ("
                    " seujet_evacuation_flow INT, arve_flow INT, leman_level NUMERIC(6,3)"
                    ") ON COMMIT DROP"
                )
                copy_sql = (
                    "COPY _stg_seujet (seujet_evacuation_flow, arve_flow, leman_level) "
                    "FROM STDIN"
                )
                async with cur.copy(copy_sql) as cp:
                    for r in rows:
                        await cp.write_row((r.seujet_evacuation_flow, r.arve_flow, r.leman_level))
                await cur.execute(
                    """
                    INSERT INTO seujet_evacuation_capacities (seujet_evacuation_flow, arve_flow, leman_level)
                    SELECT seujet_evacuation_flow, arve_flow, leman_level FROM _stg_seujet
                    ON CONFLICT (seujet_evacuation_flow, arve_flow, leman_level) DO NOTHING
                    """
                )
                return cur.rowcount or 0

                return cur.rowcount or 0

    # -------- flow_power_conversions --------
    async def upsert_flow_power(self, f: FlowPowerConversionIn) -> FlowPowerConversion:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO flow_power_conversions (dam_id, flow, group_no, power_mw, leman_level)
                    VALUES (%(dam_id)s, %(flow)s, %(group_no)s, %(power_mw)s, %(leman_level)s)
                    ON CONFLICT (dam_id, flow, group_no, leman_level) DO UPDATE SET power_mw = EXCLUDED.power_mw
                    RETURNING id, dam_id, flow, group_no, power_mw, leman_level
                    """,
                    f.__dict__,
                )
                rec = await cur.fetchone()
                return FlowPowerConversion(**rec)

    async def bulk_upsert_flow_power(self, rows: Iterable[FlowPowerConversionIn]) -> int:
        await self.ensure_open()
        rows = list(rows)
        if not rows:
            return 0
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "CREATE TEMP TABLE _stg_fpc ("
                    " dam_id INT, flow INT, group_no SMALLINT, power_mw NUMERIC(10,3), leman_level NUMERIC(6,3)"
                    ") ON COMMIT DROP"
                )
                copy_sql = (
                    "COPY _stg_fpc (dam_id, flow, group_no, power_mw, leman_level) "
                    "FROM STDIN"
                )
                async with cur.copy(copy_sql) as cp:
                    for r in rows:
                        await cp.write_row((r.dam_id, r.flow, r.group_no, r.power_mw, r.leman_level))
                await cur.execute(
                    """
                    INSERT INTO flow_power_conversions (dam_id, flow, group_no, power_mw, leman_level)
                    SELECT dam_id, flow, group_no, power_mw, leman_level FROM _stg_fpc
                    ON CONFLICT (dam_id, flow, group_no, leman_level) DO UPDATE
                        SET power_mw = EXCLUDED.power_mw
                    """
                )
                return cur.rowcount or 0
            
    async def bulk_upsert_leman_levels(self, rows: Iterable[LemanLevelIn]) -> int:
        await self.ensure_open()
        rows = list(rows)
        if not rows:
            return 0
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "CREATE TEMP TABLE _stg_leman ("
                    " leap_year BOOLEAN, month SMALLINT, day SMALLINT,"
                    " min_arve_call_level NUMERIC(6,3), max_arve_call_level NUMERIC(6,3),"
                    " min_regulation_domain NUMERIC(6,3), max_regulation_domain NUMERIC(6,3)"
                    ") ON COMMIT DROP"
                )
                copy_sql = (
                    "COPY _stg_leman (leap_year, month, day, "
                    " min_arve_call_level, max_arve_call_level, "
                    " min_regulation_domain, max_regulation_domain) "
                    "FROM STDIN"
                )
                async with cur.copy(copy_sql) as cp:
                    for r in rows:
                        await cp.write_row((
                            r.leap_year, r.month, r.day,
                            r.min_arve_call_level, r.max_arve_call_level,
                            r.min_regulation_domain, r.max_regulation_domain,
                        ))
                await cur.execute(
                    """
                    INSERT INTO leman_levels (
                        leap_year, month, day,
                        min_arve_call_level, max_arve_call_level,
                        min_regulation_domain, max_regulation_domain
                    )
                    SELECT leap_year, month, day,
                        min_arve_call_level, max_arve_call_level,
                        min_regulation_domain, max_regulation_domain
                    FROM _stg_leman
                    ON CONFLICT (leap_year, month, day) DO UPDATE SET
                        min_arve_call_level = COALESCE(EXCLUDED.min_arve_call_level, leman_levels.min_arve_call_level),
                        max_arve_call_level = COALESCE(EXCLUDED.max_arve_call_level, leman_levels.max_arve_call_level),
                        min_regulation_domain = COALESCE(EXCLUDED.min_regulation_domain, leman_levels.min_regulation_domain),
                        max_regulation_domain = COALESCE(EXCLUDED.max_regulation_domain, leman_levels.max_regulation_domain)
                    """
                )
                return cur.rowcount or 0



    async def get_power(self, *, dam_id: int, flow: int, group_no: int, leman_level: Decimal):
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, dam_id, flow, group_no, power_mw, leman_level
                    FROM flow_power_conversions
                    WHERE dam_id = %s AND flow = %s AND group_no = %s AND leman_level = %s
                    """,
                    (dam_id, flow, group_no, leman_level),
                )
                rec = await cur.fetchone()
                return FlowPowerConversion(**rec) if rec else None

    # ------------------- leman_levels -------------------
    async def upsert_leman_level(self, l: LemanLevelIn) -> LemanLevel:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO leman_levels (
                        leap_year, month, day,
                        min_arve_call_level, max_arve_call_level,
                        min_regulation_domain, max_regulation_domain
                    ) VALUES (
                        %(leap_year)s, %(month)s, %(day)s,
                        %(min_arve_call_level)s, %(max_arve_call_level)s,
                        %(min_regulation_domain)s, %(max_regulation_domain)s
                    )
                    ON CONFLICT (leap_year, month, day) DO UPDATE SET
                        min_arve_call_level = COALESCE(EXCLUDED.min_arve_call_level, leman_levels.min_arve_call_level),
                        max_arve_call_level = COALESCE(EXCLUDED.max_arve_call_level, leman_levels.max_arve_call_level),
                        min_regulation_domain = COALESCE(EXCLUDED.min_regulation_domain, leman_levels.min_regulation_domain),
                        max_regulation_domain = COALESCE(EXCLUDED.max_regulation_domain, leman_levels.max_regulation_domain)
                    RETURNING leap_year, month, day, min_arve_call_level, max_arve_call_level, min_regulation_domain, max_regulation_domain
                    """,
                    l.__dict__,
                )
                rec = await cur.fetchone()
                return LemanLevel(**rec)

    async def get_leman_level(self, *, leap_year: bool, month: int, day: int) -> Optional[LemanLevel]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT leap_year, month, day,
                           min_arve_call_level, max_arve_call_level,
                           min_regulation_domain, max_regulation_domain
                    FROM leman_levels
                    WHERE leap_year = %s AND month = %s AND day = %s
                    """,
                    (leap_year, month, day),
                )
                rec = await cur.fetchone()
                return LemanLevel(**rec) if rec else None
    
    async def get_leman_levels_for_date(self, d: date) -> Optional[LemanLevel]:
        """Retourne la ligne leman_levels correspondant à la date d (via la fonction SQL)."""
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # La fonction SQL encapsule la logique bissextile
                await cur.execute(
                    """
                    SELECT leap_year, month, day,
                           min_arve_call_level, max_arve_call_level,
                           min_regulation_domain, max_regulation_domain
                    FROM get_leman_levels_for(%s)
                    """,
                    (d,),
                )
                rec = await cur.fetchone()
                return LemanLevel(**rec) if rec else None
    
    async def get_today_leman_levels(self) -> Optional[LemanLevel]:
        from datetime import date as _date
        return await self.get_leman_levels_for_date(_date.today())

    async def get_dam_id(self, name: str) -> int | None:
        async with self.pool.connection() as conn, conn.cursor() as cur:
            await cur.execute("SELECT id FROM dams WHERE name = %s", (name,))
            row = await cur.fetchone()
            return row[0] if row else None

    async def query_power_rows(
        self,
        barrage_names: list[str],
        group: int,
        flow: int | None = None,
    ) -> list[dict]:
        """Renvoie les lignes (dict) pour les puissances (ex-`power_table`)."""
        params = {"names": barrage_names, "group_no": group}
        sql = """
            SELECT d.name,
                   f.flow        AS debit,
                   f.power_mw    AS puissance,
                   f.group_no    AS groupe,
                   f.leman_level
            FROM flow_power_conversions f
            JOIN dams d ON f.dam_id = d.id
            WHERE d.name = ANY(%(names)s)
              AND f.group_no = %(group_no)s
        """
        if flow is not None:
            flow_5 = round(flow / 5) * 5
            sql += " AND f.flow = %(flow)s"
            params["flow"] = flow_5

        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql + " ORDER BY f.flow", params)
            return await cur.fetchall()

    async def query_seujet_rows(
        self,
        group: int,
        cote_range: tuple[float, float] | None = None,
    ) -> list[dict]:
        """Renvoie les lignes (dict) Seujet pour un groupe (ex-`seujet_series`)."""
        seujet_id = await self.get_dam_id("Seujet")
        if seujet_id is None:
            return []

        params = {"dam_id": seujet_id, "group_no": group}
        sql = """
            SELECT flow AS debit,
                   group_no AS groupe,
                   power_mw AS puissance,
                   leman_level AS cote_leman
            FROM flow_power_conversions
            WHERE dam_id = %(dam_id)s AND group_no = %(group_no)s
        """
        if cote_range is not None:
            sql += " AND leman_level BETWEEN %(cmin)s AND %(cmax)s"
            params["cmin"], params["cmax"] = cote_range

        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql + " ORDER BY flow", params)
            return await cur.fetchall()

    async def list_seujet_evacuation_rows(self) -> list[dict]:
        """Renvoie toutes les lignes de la grille d’évacuation Seujet (ex-`seujet_evacuation_grid`)."""
        async with self.pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("""
                SELECT seujet_evacuation_flow AS debit_evacuation_seujet,
                       arve_flow              AS debit_arve,
                       leman_level            AS cote_leman
                FROM seujet_evacuation_capacities
            """)
            return await cur.fetchall()
        

    def _to_utc_dt(self, x):
        if isinstance(x, date) and not isinstance(x, datetime):
            x = datetime(x.year, x.month, x.day, tzinfo=timezone.utc)
        if not isinstance(x, datetime):
            raise TypeError("start/end must be datetime or date")
        if x.tzinfo is None or x.utcoffset() != timedelta(0):
            raise ValueError("start/end must be tz-aware UTC")
        return x

    def _on_grid(self, dt: datetime) -> bool:
        return (dt.minute % 15 == 0) and dt.second == 0 and dt.microsecond == 0

    async def fetch_categorical_names(self) -> List[str]:
        """List of categorical names (stable column order decided by DB)."""
        await self.ensure_open()
        async with self.pool.connection() as conn, conn.cursor() as cur:
            # force session output to UTC so timestamptz render as +00:00
            await cur.execute("SET TIME ZONE 'UTC'")
            await cur.execute("SELECT name FROM categorical ORDER BY name")
            return [r[0] for r in await cur.fetchall()]

    async def fetch_dummy_matrix_view(
        self,
        start,
        end,
    ) -> List[Dict]:
        """
        Returns wide rows from v_tuple_dummies_wide (one row per 15-min slot).
        No pandas here; just a list[dict].
        """
        s = self._to_utc_dt(start)
        e = self._to_utc_dt(end)
        if not (self._on_grid(s) and self._on_grid(e)):
            raise ValueError("start/end must align to 15-min grid")
        if e <= s:
            raise ValueError("end must be > start")

        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SET TIME ZONE 'UTC'")
                await cur.execute(
                    """
                    SELECT *
                    FROM v_tuple_dummies_wide
                    WHERE target_time >= %s AND target_time < %s
                    ORDER BY target_time
                    """,
                    (s, e),
                )
                return await cur.fetchall()

    async def fetch_dummy_matrix_long(
        self,
        start,
        end,
    ) -> List[Dict]:
        """
        Returns long rows (target_time, category) to pivot client-side.
        """
        s = self._to_utc_dt(start)
        e = self._to_utc_dt(end)
        if not (self._on_grid(s) and self._on_grid(e)):
            raise ValueError("start/end must align to 15-min grid")
        if e <= s:
            raise ValueError("end must be > start")

        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SET TIME ZONE 'UTC'")
                await cur.execute(
                    """
                    SELECT t.target_time, c.name AS category
                    FROM tuples t
                    JOIN tuple_categorical tc ON tc.tuple_id = t.id
                    JOIN categorical c        ON c.id = tc.categorical_id
                    WHERE t.target_time >= %s AND t.target_time < %s
                    ORDER BY t.target_time
                    """,
                    (s, e),
                )
                return await cur.fetchall()
    
    async def save_model(self, model_name: str, model_obj, trained_on: datetime) -> int:
        """Serialize and save model to DB, return model id."""
        await self.ensure_open()
        weights = pickle.dumps(model_obj)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                # optional: log where we're writing
                await cur.execute("SELECT current_database(), current_schema(), current_setting('search_path')")
                print("Writing to:", await cur.fetchone())
                await cur.execute(
                    """
                    INSERT INTO models (model_name, trained_on, weights)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (model_name, trained_on, weights),
                )
                (model_id,) = await cur.fetchone()
                return model_id

    async def load_latest_model(self, model_name: str) -> object | None:
        """Load the most recent model by name."""
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT weights
                    FROM models
                    WHERE model_name = %s
                    ORDER BY trained_on DESC NULLS LAST, created_at DESC
                    LIMIT 1
                    """,
                    (model_name,),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                (weights,) = row
                return pickle.loads(weights)


# ---------------- Convenience: DamsRegistry ----------------
class DamsRegistry:
    def __init__(self):
        self.by_name: dict[str, int] = {}

    async def load(self, repo: StaticsRepo) -> int:
        await repo.pool.open()
        loaded = 0
        async with repo.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SELECT id, name FROM dams ORDER BY id")
                for rec in await cur.fetchall():
                    name = (rec["name"] or "").strip()
                    if not name or name in self.by_name:
                        continue
                    self.by_name[name] = int(rec["id"])
                    loaded += 1
        return loaded

    def resolve(self, name: str) -> Optional[int]:
        return self.by_name.get((name or "").strip())
    