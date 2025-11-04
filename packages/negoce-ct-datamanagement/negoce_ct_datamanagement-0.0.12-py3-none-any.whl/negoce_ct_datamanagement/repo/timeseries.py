from __future__ import annotations

from datetime import date, datetime, time
from typing import Iterable, Optional, List, Dict, Any, Literal, Tuple, Protocol, Sequence

from psycopg.rows import dict_row

from negoce_ct_datamanagement.db_utils.connection import DbName, get_db_pool
from negoce_ct_datamanagement.models.timeseries import (
    Series, SeriesIn,
    Point, PointIn,
    LoadWindow, LoadWindowIn,
    SeriesRef
)
import asyncio

def to_datetime(x):
    # Si la vue retourne des DATE, on les élève en datetime à minuit
    if isinstance(x, date) and not isinstance(x, datetime):
        return datetime.combine(x, time.min)
    return x

class SpecLike(Protocol):
    provider: str
    data_name: str
    earliest_start: date
    end_date: Optional[date]
    area: Optional[str]


class TimeseriesRepo:
    """
    Repo unifié pour les opérations 'time series':
    - Series  : get / get_by_name / upsert / ensure_series(...)
    - Points  : write_points / get_latest / get_by_window / copy_points_csv
    - Windows : upsert_window / list_windows
    - Lookups : ensure_provider / ensure_area / ensure_domain / ensure_type / ensure_frequency / ensure_unit
    """

    _opened = False
    db_name: DbName = DbName.timeseries

    def __init__(self, db: DbName = DbName.timeseries):
        self.pool = get_db_pool(db)
    
    async def ensure_open(self):
        try:
            is_closed = bool(getattr(self.pool, "closed", False))
        except Exception:
            is_closed = True
        if self.pool is None or is_closed:
            self.pool = get_db_pool(self.db_name)
            self._opened = False

        if not self._opened:
            await self.pool.open()
            self._opened = True

    async def reset_pool(self):
        try:
            if getattr(self, "pool", None):
                try:
                    await asyncio.shield(self.pool.close())
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass
        finally:
            self.pool = get_db_pool(self.db_name)
            self._opened = False
            await self.ensure_open()    
    # -------------------------
    # SERIES (read/upsert)
    # -------------------------

    async def get_series(self, series_id: int) -> Optional[Series]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute("SELECT * FROM series WHERE id = %s", (series_id,))
                rec = await cur.fetchone()
        return Series(**rec) if rec else None

    async def get_series_by_name(self, name: str, *, area_id: Optional[int] = None) -> Optional[Series]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM series
                    WHERE name = %s
                      AND (%s IS NULL OR area_id = %s)
                    ORDER BY id
                    LIMIT 1
                    """,
                    (name, area_id, area_id),
                )
                rec = await cur.fetchone()
        return Series(**rec) if rec else None

    async def upsert_series(self, s: SeriesIn) -> Series:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO series (name, domain_id, type_id, provider_id, area_id, unit_id, frequency_id, description)
                    VALUES (%(name)s, %(domain_id)s, %(type_id)s, %(provider_id)s, %(area_id)s, %(unit_id)s, %(frequency_id)s, %(description)s)
                    ON CONFLICT (name, area_id) DO UPDATE SET
                        domain_id   = EXCLUDED.domain_id,
                        type_id     = EXCLUDED.type_id,
                        provider_id = EXCLUDED.provider_id,
                        unit_id     = EXCLUDED.unit_id,
                        frequency_id= EXCLUDED.frequency_id,
                        description = EXCLUDED.description
                    RETURNING *
                    """,
                    s.model_dump(),
                )
                rec = await cur.fetchone()
        return Series(**rec)

    # -------------------------
    # LOOKUPS (ensure)
    # -------------------------

    async def ensure_provider(self, name: str, description: Optional[str] = None) -> int:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO providers (name, description)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET description = COALESCE(EXCLUDED.description, providers.description)
                    RETURNING id
                    """,
                    (name, description),
                )
                (pid,) = await cur.fetchone()
                return pid

    async def ensure_area(self, code: str, name: Optional[str] = None) -> int:
        name = name or code
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO areas (code, name)
                    VALUES (%s, %s)
                    ON CONFLICT (code) DO UPDATE
                    SET name = COALESCE(EXCLUDED.name, areas.name)
                    RETURNING id
                    """,
                    (code, name),
                )
                (aid,) = await cur.fetchone()
                return aid

    async def ensure_domain(self, name: str) -> int:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO domains (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (name,),
                )
                (did,) = await cur.fetchone()
                return did

    async def ensure_type(self, name: str) -> int:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO series_types (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (name,),
                )
                (tid,) = await cur.fetchone()
                return tid

    async def ensure_frequency(self, name: str) -> int:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO frequencies (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (name,),
                )
                (fid,) = await cur.fetchone()
                return fid

    async def ensure_unit(self, name: str) -> int:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO units (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (name,),
                )
                (uid,) = await cur.fetchone()
                return uid

    # -------------------------
    # SERIES (ensure par ref)
    # -------------------------

    async def ensure_series(
        self,
        *,
        series_id: Optional[int],
        name: str,
        provider_name: Optional[str],
        area_code: Optional[str],
        domain_name: Optional[str],
        type_name: Optional[str],
        frequency_name: Optional[str] = None,
        unit_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Series:
        """
        Garantit l'existence d'une série correspondant à la 'ref'.

        Règles:
        - Priorité à la clé logique (name, area_id) si elle matche une série existante :
        -> on réutilise cette ligne (la DB "fait foi") et on ignore l'id fourni.
        - Si area_id est None : on adopte l'unique série trouvée par name, sinon on exige area_code.
        - Si aucune série existante n'est trouvée via (name, area_id) :
            * si series_id est fourni -> tentative d'UPDATE par id, sinon INSERT
            * INSERT avec ON CONFLICT(name, area_id) qui n'écrase que les colonnes NON NULL fournies.
        - Règle importante: si un champ est None à l'entrée, on NE modifie PAS la colonne existante.
        """

        # 1) Lookups (créés au besoin)
        provider_id  = await self.ensure_provider(provider_name, None) if provider_name   else None
        area_id      = await self.ensure_area(area_code)               if area_code       else None
        domain_id    = await self.ensure_domain(domain_name)           if domain_name     else None
        type_id      = await self.ensure_type(type_name)               if type_name       else None
        frequency_id = await self.ensure_frequency(frequency_name)     if frequency_name  else None
        unit_id      = await self.ensure_unit(unit_name)               if unit_name       else None

        await self.ensure_open()
        async with self.pool.connection() as conn:

            # 2) Pré-résolution par (name, area_id) : si une série existe déjà pour ce couple,
            #    on la réutilise et on ignore l'id fourni dans le payload.
            existing: Optional[Series] = None
            async with conn.cursor(row_factory=dict_row) as cur:
                if area_id is not None:
                    # Match exact sur (name, area_id)
                    await cur.execute(
                        "SELECT * FROM series WHERE name = %s AND area_id = %s LIMIT 1",
                        (name, area_id),
                    )
                    row = await cur.fetchone()
                    if row:
                        existing = Series(**row)
                else:
                    # area inconnue -> on n'adopte que si le nom est unique
                    await cur.execute(
                        "SELECT * FROM series WHERE name = %s ORDER BY id LIMIT 2",
                        (name,),
                    )
                    rows = await cur.fetchall()
                    if len(rows) == 1:
                        existing = Series(**rows[0])
                    elif len(rows) > 1:
                        raise ValueError(
                            f"Plusieurs séries nommées '{name}' existent avec des zones différentes : "
                            f"fournis area_code pour désambigüer."
                        )

            if existing:
                # Mettre à jour 'non-NULL only' la ligne existante et la retourner
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        """
                        UPDATE series
                        SET
                            -- name obligatoire -> mis à jour explicitement
                            name         = %s,
                            -- colonnes optionnelles: n'écraser que si valeur NON NULL fournie
                            domain_id    = COALESCE(%s, domain_id),
                            type_id      = COALESCE(%s, type_id),
                            provider_id  = COALESCE(%s, provider_id),
                            area_id      = COALESCE(%s, area_id),
                            unit_id      = COALESCE(%s, unit_id),
                            frequency_id = COALESCE(%s, frequency_id),
                            description  = COALESCE(%s, description)
                        WHERE id = %s
                        RETURNING *
                        """,
                        (
                            name,
                            domain_id, type_id, provider_id, area_id, unit_id, frequency_id, description,
                            existing.id,
                        ),
                    )
                    rec = await cur.fetchone()
                    return Series(**rec)

            # 3) Aucune série trouvée par (name, area_id) -> on applique l'ancienne logique :
            #    3a) Si series_id fourni: tentative d'UPDATE direct par id
            if series_id is not None:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        """
                        UPDATE series
                        SET
                            name         = %s,
                            domain_id    = COALESCE(%s, domain_id),
                            type_id      = COALESCE(%s, type_id),
                            provider_id  = COALESCE(%s, provider_id),
                            area_id      = COALESCE(%s, area_id),
                            unit_id      = COALESCE(%s, unit_id),
                            frequency_id = COALESCE(%s, frequency_id),
                            description  = COALESCE(%s, description)
                        WHERE id = %s
                        RETURNING *
                        """,
                        (
                            name,
                            domain_id, type_id, provider_id, area_id, unit_id, frequency_id, description,
                            series_id,
                        ),
                    )
                    rec = await cur.fetchone()
                    if rec:
                        return Series(**rec)

            #    3b) Sinon on insère (avec ou sans id explicite), en upsertant sur (name, area_id)
            async with conn.cursor(row_factory=dict_row) as cur:
                if series_id is not None:
                    # tentative d'INSERT avec id fourni
                    await cur.execute(
                        """
                        INSERT INTO series
                            (id, name, domain_id, type_id, provider_id, area_id, unit_id, frequency_id, description)
                        OVERRIDING SYSTEM VALUE
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (name, area_id) DO UPDATE SET
                            domain_id    = COALESCE(EXCLUDED.domain_id,    series.domain_id),
                            type_id      = COALESCE(EXCLUDED.type_id,      series.type_id),
                            provider_id  = COALESCE(EXCLUDED.provider_id,  series.provider_id),
                            unit_id      = COALESCE(EXCLUDED.unit_id,      series.unit_id),
                            frequency_id = COALESCE(EXCLUDED.frequency_id, series.frequency_id),
                            description  = COALESCE(EXCLUDED.description,  series.description)
                        RETURNING *
                        """
                        ,
                        (series_id, name, domain_id, type_id, provider_id, area_id, unit_id, frequency_id, description),
                    )
                else:
                    await cur.execute(
                        """
                        INSERT INTO series
                            (name, domain_id, type_id, provider_id, area_id, unit_id, frequency_id, description)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (name, area_id) DO UPDATE SET
                            domain_id    = COALESCE(EXCLUDED.domain_id,    series.domain_id),
                            type_id      = COALESCE(EXCLUDED.type_id,      series.type_id),
                            provider_id  = COALESCE(EXCLUDED.provider_id,  series.provider_id),
                            unit_id      = COALESCE(EXCLUDED.unit_id,      series.unit_id),
                            frequency_id = COALESCE(EXCLUDED.frequency_id, series.frequency_id),
                            description  = COALESCE(EXCLUDED.description,  series.description)
                        RETURNING *
                        """
                        ,
                        (name, domain_id, type_id, provider_id, area_id, unit_id, frequency_id, description),
                    )
                rec = await cur.fetchone()
                return Series(**rec)



    # -------------------------
    # POINTS
    # -------------------------

    async def write_points(self, series_id: int, points: Iterable[PointIn]) -> int:
        """
        Insère des points (issue_time par défaut NOW()).
        Conflit sur (series_id, target_time, issue_time) -> DO NOTHING.
        """
        await self.ensure_open()
        items = [p.model_dump() for p in points]
        for it in items:
            if it.get("issue_time") is None:
                it["issue_time"] = None  # laisser la DB mettre NOW()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(
                    """
                    INSERT INTO points (series_id, target_time, value, issue_time)
                    VALUES (%(series_id)s, %(target_time)s, %(value)s, COALESCE(%(issue_time)s, NOW()))
                    ON CONFLICT (series_id, target_time, value)
                    DO UPDATE SET issue_time = EXCLUDED.issue_time
                    """,
                    [{"series_id": series_id, **it} for it in items],
                )
                return max(cur.rowcount or 0, 0)

    async def copy_points_csv(self, data: bytes, *, with_issue_time: bool) -> int:
        """
        COPY CSV massivement via une table temporaire pour pouvoir appliquer
        ensuite un INSERT ... ON CONFLICT (comme dans write_points).
        - with_issue_time=True  -> colonnes (series_id, target_time, value, issue_time)
        - with_issue_time=False -> colonnes (series_id, target_time, value) ; issue_time = now()
        Retourne le nombre de lignes affectées par l'INSERT.
        """
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                # 1) Création d'une table temporaire adaptée
                if with_issue_time:
                    await cur.execute(
                        """
                        CREATE TEMP TABLE tmp_points (
                            series_id INT,
                            target_time TIMESTAMPTZ,
                            value DOUBLE PRECISION,
                            issue_time TIMESTAMPTZ
                        ) ON COMMIT DROP
                        """
                    )
                    copy_sql = "COPY tmp_points (series_id, target_time, value, issue_time) FROM STDIN WITH (FORMAT csv)"
                else:
                    await cur.execute(
                        """
                        CREATE TEMP TABLE tmp_points (
                            series_id INT,
                            target_time TIMESTAMPTZ,
                            value DOUBLE PRECISION
                        ) ON COMMIT DROP
                        """
                    )
                    copy_sql = "COPY tmp_points (series_id, target_time, value) FROM STDIN WITH (FORMAT csv)"

                # 2) COPY dans la table temporaire
                async with cur.copy(copy_sql) as cp:
                    await cp.write(data)

                # 3) INSERT depuis la temp table en appliquant la logique ON CONFLICT
                if with_issue_time:
                    await cur.execute(
                        """
                        INSERT INTO points (series_id, target_time, value, issue_time)
                        SELECT series_id, target_time, value, issue_time FROM tmp_points
                        ON CONFLICT (series_id, target_time, value)
                        DO UPDATE SET issue_time = EXCLUDED.issue_time

                        """
                    )
                else:
                    await cur.execute(
                        """
                        INSERT INTO points (series_id, target_time, value)
                        SELECT series_id, target_time, value FROM tmp_points
                        ON CONFLICT (series_id, target_time, value)
                        DO UPDATE SET issue_time = EXCLUDED.issue_time
                        """
                    )

                inserted = cur.rowcount or 0

        return inserted

    async def get_points_latest(
        self,
        series_id: int,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[Point]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT series_id, target_time, value, issue_time
                    FROM v_points_latest
                    WHERE series_id = %s
                      AND (%s IS NULL OR target_time >= %s)
                      AND (%s IS NULL OR target_time <  %s)
                    ORDER BY target_time
                    """,
                    (series_id, start, start, end, end),
                )
                rows = await cur.fetchall()
        return [Point(**r) for r in rows]

    async def get_points_by_window(
        self,
        series_id: int,
        *,
        window_name: str = "all",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        frequency: Optional[str] = None,   
    ) -> list[Point]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    "SELECT * FROM get_points_by_window(%s, %s, %s, %s, %s) ORDER BY target_time",
                    (series_id, window_name, start, end, (frequency or 'raw')),
                )
                rows = await cur.fetchall()
        return [Point(series_id=series_id, **r) for r in rows]

    # -------------------------
    # WINDOWS
    # -------------------------

    async def upsert_window(self, w: LoadWindowIn) -> LoadWindow:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO load_windows (name, area_id, dow, start_time, end_time, include_holidays, timezone)
                    VALUES (%(name)s, %(area_id)s, %(dow)s, %(start_time)s, %(end_time)s, %(include_holidays)s, %(timezone)s)
                    ON CONFLICT (name, area_id, dow, start_time, end_time) DO UPDATE SET
                        include_holidays = EXCLUDED.include_holidays,
                        timezone = EXCLUDED.timezone
                    RETURNING *
                    """,
                    w.model_dump(),
                )
                rec = await cur.fetchone()
        return LoadWindow(**rec)

    async def list_windows(
        self,
        *,
        area_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> list[LoadWindow]:
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT *
                    FROM load_windows
                    WHERE (%s IS NULL OR area_id = %s)
                      AND (%s IS NULL OR name = %s)
                    ORDER BY area_id, name
                    """,
                    (area_id, area_id, name, name),
                )
                rows = await cur.fetchall()
        return [LoadWindow(**r) for r in rows]
    
    async def get_references(self) -> List[SeriesRef]:
        """
        Récupère toutes les séries avec noms résolus
        (domain, type, provider, area, unit, frequency).
        Renvoie une liste de SeriesRef (Pydantic).
        """
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT
                        s.id,
                        s.name,
                        st.name AS type,
                        p.name  AS provider,
                        d.name  AS domain,
                        a.code  AS area,
                        u.name  AS unit,
                        f.name  AS frequency,
                        v.start_date,
                        v.end_date,
                        v.historical_start,
                        s.description
                    FROM series s
                    LEFT JOIN series_types st ON st.id = s.type_id
                    LEFT JOIN providers p     ON p.id  = s.provider_id
                    LEFT JOIN domains d       ON d.id  = s.domain_id
                    LEFT JOIN areas a         ON a.id  = s.area_id
                    LEFT JOIN units u         ON u.id  = s.unit_id
                    LEFT JOIN frequencies f   ON f.id  = s.frequency_id
                    LEFT JOIN v_series_fetch_window v ON v.series_id = s.id
                    ORDER BY s.id;
                    """
                )
                rows = await cur.fetchall()

        return [
            SeriesRef(
                id=r["id"],
                name=r["name"],
                type=r["type"] or "actual",
                provider=r["provider"] or "",
                domain=r["domain"] or "unknown",
                area=r["area"] or "UNK",
                unit=r["unit"] or "",
                frequency=r["frequency"] or "",
                description=r["description"] or "",
                start_date=r["start_date"],
                end_date=r["end_date"],
                historical_start=r["historical_start"]
            )
            for r in rows
        ]
    
    # -------------------------
    # NET POSITION
    # -------------------------

    async def materialize_net_position_hourly(
            self,
            *,
            window_name: str = "all",                 
            area_code: str = "CH",
            target_series_name: str = "net_position_hourly_all",
            start: Optional[datetime] = None,          # si fourni, on ignore backfill_hours
            end: Optional[datetime] = None,            # défaut: now() côté DB
            backfill_hours: int = 26,                  # si start/end non fournis: maintenant - 26h → maintenant
            # Création auto de la série si absente :
            create_series_if_missing: bool = True,
            provider_name: str = "DB-Computed",
            domain_name: str = "Power",
            type_name: str = "derived",
            frequency_name: str = "hourly",
            unit_name: str = "MW",
            area_name_if_new: Optional[str] = None,
            description: str = "Σ production - consommation (moyenne horaire)",
            require_full_coverage: bool = True,       
            min_series_coverage: float = 1.0,         
            on_gap: str = "skip",
        ) -> int:
            """
            Matérialise la Net Position *horaire* dans la série cible (insert dans points).
            Retourne le nombre de lignes insérées.

            Hypothèses :
            - La DB expose la fonction get_net_position_hourly(window_name, from, to)
                qui combine PV/Hydro/UIC/Hedge/Conso via series_roles + fenêtres load_windows.
            - La vue v_points_latest existe (gestion des 'versions' par issue_time).
            """
            # 1) S'assure que la série cible existe (idempotent)
            if create_series_if_missing:
                _ = await self.ensure_series(
                    series_id=None,
                    name=target_series_name,
                    provider_name=provider_name,
                    area_code=area_code,
                    domain_name=domain_name,
                    type_name=type_name,
                    frequency_name=frequency_name,
                    unit_name=unit_name,
                    description=description,
                )

            await self.ensure_open()
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:

                    # 2) On récupère l'ID de la série cible
                    await cur.execute(
                        """
                        SELECT s.id AS series_id
                        FROM series s
                        JOIN areas a ON a.id = s.area_id
                        WHERE s.name = %s AND a.code = %s
                        LIMIT 1
                        """,
                        (target_series_name, area_code),
                    )
                    sid_row = await cur.fetchone()
                    if not sid_row:
                        raise ValueError(
                            f"Série cible introuvable: name='{target_series_name}', area='{area_code}'. "
                            f"create_series_if_missing={create_series_if_missing}"
                        )
                    series_id = sid_row["series_id"]

                    # 3) Paramétrage de la fenêtre temporelle
                    #    - si start non fourni → on utilise une fenêtre glissante 'backfill_hours'
                    if start is None:
                        # On laisse 'end' NULL côté SQL (= now()) pour éviter le décalage py/db
                        sql_time_clause = "now() - INTERVAL %s, NULL"
                        time_params = (f"{backfill_hours} hours",)
                    else:
                        # On passe start & end explicitement (end peut rester NULL → now() côté SQL)
                        sql_time_clause = "%s, %s"
                        time_params = (start, end)

                    # 4) INSERT … SELECT depuis la fonction DB
                    #    - On insère la *version* courante avec issue_time = now()
                    #    - Idempotence partielle: si le même job relance *à la même seconde*, même issue_time → DO NOTHING
                    #      (sinon, nouvelle version → visible via v_points_latest)
                    sql = f"""
                        WITH data AS (
                            SELECT ts_hour AS target_time, net_value AS value
                            FROM get_net_position_hourly(
                                %s,                     -- p_window_name
                                {sql_time_clause},      -- p_from, p_to
                                %s,                     -- p_require_full_coverage
                                %s,                     -- p_min_series_coverage
                                %s                      -- p_on_gap
                            )
                        )
                        INSERT INTO points (series_id, target_time, value, issue_time)
                        SELECT %s, d.target_time, d.value, now()
                        FROM data d
                        WHERE d.value IS NOT NULL
                        ON CONFLICT (series_id, target_time, value)
                        DO UPDATE SET issue_time = EXCLUDED.issue_time
                    """
                    params = (
                        window_name,
                        *time_params,
                        require_full_coverage,
                        min_series_coverage,
                        on_gap,
                        series_id,
                    )
                    await cur.execute(sql, params)
                    inserted = cur.rowcount or 0

            return inserted
    
    async def get_net_position_from_hourly(
        self,
        *,
        series_name: str = "net_position_hourly_all",
        area_code: str = "CH",
        window_name: str = "all",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        freq: Literal["day", "week"] = "day",
        measure: Literal["power", "energy"] = "power", 
    ) -> List[Dict[str, Any]]:
        """
        Agrège la net position *stockée à l'heure* vers jour/semaine.
        Retour: [{"date": datetime, "value": float}, ...]
        """
        await self.ensure_open()
        sql = """
            SELECT ts, value
            FROM get_net_position_from_hourly(%s,%s,%s,%s,%s,%s,%s)
            ORDER BY ts
        """
        params = (series_name, area_code, window_name, start, end, freq, measure)
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
        return [{"date": r["ts"], "value": r["value"]} for r in rows]

    async def get_net_position_weeks_from_hourly(
        self,
        *,
        series_name: str = "net_position_hourly_all",
        area_code: str = "CH",
        window_name: str = "all",
        week0: date = None,
        weeks: int = 4,
        weekends: bool = False,
        measure: Literal["power", "energy"] = "power",
    ) -> List[Dict[str, Any]]:
        """
        W1..Wn (option week-ends) agrégés depuis la série horaire.
        Retour: [{"week_index": int, "week_start": date, "value": float}, ...]
        """
        if week0 is None:
            raise ValueError("week0 (date) est requis")
        await self.ensure_open()
        sql = """
            SELECT week_index, week_start, value
            FROM get_net_position_weeks_from_hourly(%s,%s,%s,%s,%s,%s,%s)
            ORDER BY week_index
        """
        params = (series_name, area_code, window_name, week0, weeks, weekends, measure)
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
        return [
            {"week_index": r["week_index"], "week_start": r["week_start"], "value": r["value"]}
            for r in rows
        ]
    
    async def materialize_monetary_exposure_hourly_all(
        self,
        *,
        area_code: str = "CH",
        target_series_name: str = "Monetary Exposure hourly (all)",
        np_series_name: str = "net_position_hourly_all",
        price_series_name: str = "pri ch spot ecmonthly €/mwh cet h f [Avg]",
        start: Optional[datetime] = None,     # si fourni, backfill_hours est ignoré
        end: Optional[datetime] = None,       # peut rester None -> now() côté DB
        backfill_hours: int = 26,             # si start/end non fournis: now()-26h .. now()
        create_series_if_missing: bool = True,
        provider_name: str = "DB-Computed",
        domain_name: str = "Finance",         # adapte selon tes nomenclatures de domain
        type_name: str = "derived",
        frequency_name: str = "hourly",
        unit_name: str = "EUR",
        area_name_if_new: Optional[str] = None,
        description: str = "net_position_hourly_all × pri ch spot ecmonthly €/mwh cet h f [Avg] (EUR/h)",
    ) -> int:
        """
        Matérialise l'exposition monétaire *horaire* (mode 'all' uniquement) en insérant
        dans `points` les données renvoyées par la fonction SQL
        `get_monetary_exposure_hourly_all`.

        Paramètres:
          - area_code: code de zone (ex. 'CH')
          - target_series_name: série cible à écrire (EUR, hourly)
          - np_series_name: nom de la série 'net_position_hourly_all'
          - price_series_name: nom de la série 'pri ch spot ecmonthly €/mwh cet h f [Avg]'
          - start/end OU backfill_hours pour définir l'intervalle
          - create_series_if_missing: crée/assure la série cible si absente (provider/domain/...)
        Retour:
          - nombre de lignes insérées dans `points`
        """
        # 1) S'assurer que la série cible existe (idempotent)
        if create_series_if_missing:
            _ = await self.ensure_series(
                series_id=None,
                name=target_series_name,
                provider_name=provider_name,
                area_code=area_code,
                domain_name=domain_name,
                type_name=type_name,
                frequency_name=frequency_name,
                unit_name=unit_name,
                description=description,
            )

        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                # 2) Récupère l'id de la série cible
                await cur.execute(
                    """
                    SELECT s.id AS series_id
                    FROM series s
                    JOIN areas a ON a.id = s.area_id
                    WHERE s.name = %s AND a.code = %s
                    LIMIT 1
                    """,
                    (target_series_name, area_code),
                )
                row = await cur.fetchone()
                if not row:
                    raise ValueError(
                        f"Série cible introuvable: name='{target_series_name}', area='{area_code}'. "
                        f"create_series_if_missing={create_series_if_missing}"
                    )
                series_id = row["series_id"]

                # 3) Préparer la clause temporelle
                #    - si start est None -> fenêtre glissante (backfill_hours)
                if start is None:
                    time_clause = "now() - INTERVAL %s, NULL"
                    time_params = (f"{backfill_hours} hours",)
                else:
                    time_clause = "%s, %s"
                    time_params = (start, end)

                # 4) INSERT … SELECT depuis la fonction SQL
                sql = f"""
                    WITH data AS (
                        SELECT ts_hour AS target_time, exposure AS value
                        FROM get_monetary_exposure_hourly_all(%s, %s, %s, {time_clause})
                    )
                    INSERT INTO points (series_id, target_time, value, issue_time)
                    SELECT %s, d.target_time, d.value, now()
                    FROM data d
                    ON CONFLICT (series_id, target_time, value)
                    DO UPDATE SET issue_time = EXCLUDED.issue_time

                """
                params = (
                    np_series_name,
                    price_series_name,
                    area_code,
                    *time_params,
                    series_id,
                )
                await cur.execute(sql, params)
                inserted = cur.rowcount or 0

        return inserted
    
    async def get_monetary_exposure_hourly_all(
        self,
        *,
        np_series_name: str = "net_position_hourly_all",
        price_series_name: str = "pri ch spot ecmonthly €/mwh cet h f [Avg]",
        area_code: str = "CH",
        window_name: str = "all",                 
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        await self.ensure_open()
        sql = """
            SELECT ts_hour, exposure
            FROM get_monetary_exposure_hourly_all(%s, %s, %s, %s, %s, %s)
            ORDER BY ts_hour
        """
        params = (np_series_name, price_series_name, area_code, window_name, start, end)
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
        return [{"date": to_datetime(r["ts_hour"]), "exposure": r["exposure"]} for r in rows]

    async def get_monetary_exposure_agg_all(
        self,
        *,
        np_series_name: str = "net_position_hourly_all",
        price_series_name: str = "pri ch spot ecmonthly €/mwh cet h f [Avg]",
        area_code: str = "CH",
        window_name: str = "all",                  # ⬅️ ajouté
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        freq: Literal["day", "week"] = "day",
    ) -> List[Dict[str, Any]]:
        await self.ensure_open()
        sql = """
            SELECT ts, exposure
            FROM get_monetary_exposure_agg_all(%s, %s, %s, %s, %s, %s, %s)
            ORDER BY ts
        """
        params = (np_series_name, price_series_name, area_code, window_name, start, end, freq)
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
        return [{"date": to_datetime(r["ts"]), "exposure": r["exposure"]} for r in rows]

    async def get_monetary_exposure_weeks_all(
        self,
        *,
        np_series_name: str = "net_position_hourly_all",
        price_series_name: str = "pri ch spot ecmonthly €/mwh cet h f [Avg]",
        area_code: str = "CH",
        window_name: str = "all",                 
        week0: date,
        weeks: int = 4,
        weekends: bool = False,
    ) -> List[Dict[str, Any]]:
        if week0 is None:
            raise ValueError("week0 (date) est requis")
        await self.ensure_open()
        sql = """
            SELECT week_index, week_start, exposure
            FROM get_monetary_exposure_weeks_all(%s, %s, %s, %s, %s, %s, %s)
            ORDER BY week_index
        """
        params = (np_series_name, price_series_name, area_code, window_name, week0, weeks, weekends)
        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()
        return [
            {"week_index": r["week_index"], "week_start": r["week_start"], "exposure": r["exposure"]}
            for r in rows
        ]

    async def get_points_bundle_day(
        self,
        *,
        series_ids_by_key: Dict[str, int],
        start: Optional[datetime],
        end: Optional[datetime],
        windows: Sequence[str] = ("all", "peak", "off-peak"),
    ) -> List[Dict[str, Any]]:
        """
        Récupère en une SEULE requête SQL les valeurs J+1 (freq 'day')
        pour plusieurs séries et plusieurs fenêtres (all/peak/off-peak).

        Args:
            series_ids_by_key: ex {"net": 123, "exp": 456, "spot": 789}
            start, end: bornes temporelles
            windows: fenêtres à interroger (défaut: all/peak/off-peak)

        Returns:
            [{"key": "net", "window": "all", "date": <dt>, "value": <float>}, ...]
        """
        await self.ensure_open()

        keys: Tuple[str, ...] = tuple(series_ids_by_key.keys())
        ids:  Tuple[int,  ...] = tuple(series_ids_by_key.values())
        wins: Tuple[str,  ...] = tuple(windows)

        sql = """
            WITH series as (
                SELECT UNNEST(%s::text[])  AS key,
                    UNNEST(%s::int[])   AS sid
            ),
            wins AS (
                SELECT UNNEST(%s::text[])  AS window_name
            )
            SELECT s.key,
                w.window_name AS window,
                x.target_time::timestamp AS ts,
                x.value::double precision AS value
            FROM series s
            CROSS JOIN wins w
            JOIN LATERAL (
                SELECT target_time, value
                FROM get_points_by_window(s.sid, w.window_name, %s, %s, 'day')
            ) AS x ON TRUE
            ORDER BY s.key, w.window_name, ts
        """
        params = (list(keys), list(ids), list(wins), start, end)

        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()

        return [
            {"key": r["key"], "window": r["window"], "date": to_datetime(r["ts"]), "value": r["value"]}
            for r in rows
        ]
    
    async def get_points_bundle_hour(
        self,
        *,
        series_ids_by_key: Dict[str, int],
        start: Optional[datetime],
        end: Optional[datetime],
        windows: Sequence[str] = ("all", "peak", "off-peak"),
    ) -> List[Dict[str, Any]]:
        """
        Récupère en une seule requête SQL les valeurs horaires (freq 'hour')
        pour plusieurs séries et fenêtres.

        Returns:
            [{"key": "pv", "window": "all", "date": <dt>, "value": <float>}, ...]
        """
        await self.ensure_open()

        keys: Tuple[str, ...] = tuple(series_ids_by_key.keys())
        ids:  Tuple[int,  ...] = tuple(series_ids_by_key.values())
        wins: Tuple[str,  ...] = tuple(windows)

        sql = """
            WITH series as (
                SELECT UNNEST(%s::text[])  AS key,
                    UNNEST(%s::int[])   AS sid
            ),
            wins AS (
                SELECT UNNEST(%s::text[])  AS window_name
            )
            SELECT s.key,
                w.window_name AS window,
                x.target_time::timestamp AS ts,
                x.value::double precision AS value
            FROM series s
            CROSS JOIN wins w
            JOIN LATERAL (
                SELECT target_time, value
                FROM get_points_by_window(s.sid, w.window_name, %s, %s, 'hour')
            ) AS x ON TRUE
            ORDER BY s.key, w.window_name, ts
        """
        params = (list(keys), list(ids), list(wins), start, end)

        async with self.pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(sql, params)
                rows = await cur.fetchall()

        return [
            {"key": r["key"], "window": r["window"], "date": to_datetime(r["ts"]), "value": r["value"]}
            for r in rows
        ]


    # -------------------------
    # Date Series Table for get_data_combined
    # -------------------------
    async def bulk_upsert_series_dates(
        self,
        rows: Iterable[Tuple[int, date, Optional[date], date]],
    ) -> int:
        """
        rows = iterable of (series_id, start_date, end_date_or_None, historical_start)
        """
        await self.ensure_open()
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                rows = list(rows)
                if not rows:
                    return 0
                await cur.executemany(
                    """
                    INSERT INTO series_date (series_id, start_date, end_date, historical_start)
                    VALUES (%s, %s, COALESCE(%s, 'infinity'::date), %s)
                    ON CONFLICT (series_id) DO UPDATE SET
                        start_date       = EXCLUDED.start_date,
                        end_date         = EXCLUDED.end_date,
                        historical_start = EXCLUDED.historical_start
                    """,
                    rows,
                )
                return cur.rowcount or 0