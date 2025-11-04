import os
from enum import Enum
from pathlib import Path
from typing import Dict

from psycopg import conninfo
from psycopg_pool import AsyncConnectionPool
from dotenv import load_dotenv, find_dotenv


class Env(str, Enum):
    dev = "development"
    test = "testing"
    prod = "production"


class DbName(str, Enum):
    statics = "statics"
    timeseries = "timeseries"


_POOLS: Dict[DbName, AsyncConnectionPool] = {}

def _require_env(var: str) -> str:
    val = os.getenv(var)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {var}")
    return val


def _build_conninfo(db_name: str) -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        print(f"Using DATABASE_URL for {db_name}")
        print(f"  {url=}")
        return conninfo.make_conninfo(url, dbname=db_name)
    print(f"Building connection info for {db_name} from individual env vars")
    print(f"  POSTGRESQL_USER={_require_env('POSTGRESQL_USER')}")
    print(f"  POSTGRESQL_HOST={_require_env('POSTGRESQL_HOST')}")
    print(f"  POSTGRESQL_PORT={_require_env('POSTGRESQL_PORT')}")
    return conninfo.make_conninfo(
        dbname=db_name,
        user=_require_env("POSTGRESQL_USER"),
        password=_require_env("POSTGRESQL_PASSWORD"),
        host=_require_env("POSTGRESQL_HOST"),
        port=_require_env("POSTGRESQL_PORT"),
        sslmode=os.getenv("POSTGRESQL_SSLMODE", "prefer"),
    )



def get_db_pool(
    db_name: DbName,
    *,
    min_size: int = 1,
    max_size: int = 30,
    autocommit: bool = False,
) -> AsyncConnectionPool:
    """
    Retourne un AsyncConnectionPool mis en cache pour `db_name`.
    - Si un pool est présent dans le cache mais *fermé* (ou invalide), on l'éjecte et on en recrée un.
    - Les pools sont créés avec open=False : le code appelant doit faire `await pool.open()` une fois.
    """

    pool = _POOLS.get(db_name)

    if pool is not None:
        try:
            is_closed = bool(getattr(pool, "closed", False))
        except Exception:
            is_closed = True

        if is_closed:
            _POOLS.pop(db_name, None)
            pool = None

    if pool is None:
        ci = _build_conninfo(db_name.value)

        async def _configure(conn, _autocommit=autocommit):
            await conn.set_autocommit(True)
            async with conn.cursor() as cur:
                await cur.execute("SET statement_timeout = '10s'")
            await conn.set_autocommit(_autocommit)

        env_min = os.getenv(f"{db_name.value.upper()}_POOL_MIN")
        env_max = os.getenv(f"{db_name.value.upper()}_POOL_MAX")
        if env_min:
            try:
                min_size = int(env_min)
            except ValueError:
                pass
        if env_max:
            try:
                max_size = int(env_max)
            except ValueError:
                pass

        pool = AsyncConnectionPool(
            ci,
            min_size=min_size,
            max_size=max_size,
            timeout=10,
            open=False, 
            name=f"{db_name.value}-pool-{os.getpid()}",
            configure=_configure,
        )
        _POOLS[db_name] = pool

    return pool

async def open_all_pools(dbs: DbName) -> None:
    for db in dbs:
        pool = get_db_pool(db)
        await pool.open()


async def close_all_pools() -> None:
    for name, pool in list(_POOLS.items()):
        try:
            await pool.close()
        finally:
            _POOLS.pop(name, None) 