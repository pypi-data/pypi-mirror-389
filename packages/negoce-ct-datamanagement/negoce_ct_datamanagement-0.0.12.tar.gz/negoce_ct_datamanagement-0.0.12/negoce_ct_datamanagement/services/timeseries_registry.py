from __future__ import annotations

from typing import Dict, Tuple, Optional, Sequence, Callable, Protocol, cast
from dataclasses import dataclass
import logging
import asyncio
from datetime import date, datetime
from fastapi import FastAPI

from negoce_ct_datamanagement.db_utils.connection import DbName
from negoce_ct_datamanagement.repo.timeseries import TimeseriesRepo
from negoce_ct_datamanagement.models.timeseries import SeriesRef

logger = logging.getLogger(__name__)

# ---------- Contrat repo ----------
class HasGetReferences(Protocol):
    async def get_references(self) -> list[SeriesRef]: ...

RepoFactory = Callable[[], HasGetReferences]

def _default_repo_factories() -> Dict[DbName, RepoFactory]:
    return {DbName.timeseries: lambda: TimeseriesRepo(DbName.timeseries)}

# ---------- Objet registre réutilisable ----------
@dataclass(frozen=True)
class TimeseriesRegistry:
    timeseries_map: Dict[Tuple[str, str], int]
    timeseries_by_id: Dict[int, SeriesRef]
    timeseries_by_provider: Dict[str, Dict[str, SeriesRef]]
    timeseries_map_date: Dict[Tuple[str, str], Dict[str, date]]

    def resolve_series_id(self, provider: str, name: str) -> Optional[int]:
        key = ((provider or "").strip(), (name or "").strip())
        return self.timeseries_map.get(key)

    def get_series_ref_by_id(self, series_id: int) -> Optional[SeriesRef]:
        return self.timeseries_by_id.get(series_id)

# ---------- Cœur unique : construit le registre ----------
async def build_timeseries_registry(
    *,
    dbs: Sequence[DbName] = (DbName.timeseries,),
    repo_factories: Optional[Dict[DbName, RepoFactory]] = None,
) -> TimeseriesRegistry:
    factories = {**_default_repo_factories(), **(repo_factories or {})}

    ts_map: Dict[Tuple[str, str], int] = {}
    ts_map_date: Dict[Tuple[str, str], Dict[str, date]] = {}
    ts_by_id: Dict[int, SeriesRef] = {}
    ts_by_provider: Dict[str, Dict[str, SeriesRef]] = {}

    async def _load_one(db: DbName) -> int:
        if db not in factories:
            raise RuntimeError(
                f"Aucune factory de repo enregistrée pour DbName={db}. "
                "Passe-la via `repo_factories`."
            )
        repo = factories[db]()
        refs = await repo.get_references()

        loaded = 0
        for ref in refs:
            provider = (ref.provider or "").strip()
            name = (ref.name or "").strip()
            
            if provider == "Volue" and "pro ch tot mwh/h cet min15 a" in name:
                logger.warning(
                    "👀 Found target ref: id=%s, provider=%s, name=%s, start_date=%s, end_date=%s, historical_start=%s",
                    ref.id, provider, name, ref.start_date, ref.end_date, ref.historical_start,
                )

            if not provider or not name:
                logger.warning("Ignore série sans provider ou name (db=%s, id=%s).", db, getattr(ref, "id", None))
                continue

            key = (provider, name)
            if key in ts_map:
                logger.warning(
                    "Doublon détecté pour (provider=%r, name=%r) — on conserve la première occurrence.",
                    provider, name
                )
                continue

            ts_map[key] = ref.id
            ts_map_date[key] = {"start_date":ref.start_date, "end_date": ref.end_date, "historical_start": ref.historical_start}
            ts_by_id[ref.id] = ref
            ts_by_provider.setdefault(provider, {})[name] = ref
            loaded += 1

        logger.info("Loaded %s timeseries from %s.", loaded, db)
        return loaded

    total_loaded = 0
    for db in dbs:
        try:
            total_loaded += await _load_one(db)
        except Exception as e:
            logger.exception("Erreur lors du chargement des séries depuis %s: %s", db, e)

    logger.info("Final merged map contains %s timeseries.", len(ts_map))
    logger.debug("Total loaded across DBs: %s", total_loaded)

    return TimeseriesRegistry(
        timeseries_map=ts_map,
        timeseries_map_date=ts_map_date,
        timeseries_by_id=ts_by_id,
        timeseries_by_provider=ts_by_provider,
    )

# ---------- API “dict” : mince enveloppe autour du cœur ----------
async def load_timeseries_registry_dict(
    *,
    dbs: Sequence[DbName] = (DbName.timeseries,),
    repo_factories: Optional[Dict[DbName, RepoFactory]] = None,
) -> Dict[str, Dict]:
    reg = await build_timeseries_registry(dbs=dbs, repo_factories=repo_factories)
    return {
        "timeseries_map": reg.timeseries_map,
        "timeseries_map_date": reg.timeseries_map_date,
        "timeseries_by_id": reg.timeseries_by_id,
        "timeseries_by_provider": reg.timeseries_by_provider,
    }

def load_timeseries_registry_dict_sync(
    *,
    dbs: Sequence[DbName] = (DbName.timeseries,),
    repo_factories: Optional[Dict[DbName, RepoFactory]] = None,
) -> Dict[str, Dict]:
    return asyncio.run(load_timeseries_registry_dict(dbs=dbs, repo_factories=repo_factories))

# ---------- Version FastAPI : se contente d’appeler le cœur et de pousser dans app.state ----------
async def load_timeseries_registry_app(
    app: FastAPI,
    *,
    dbs: Sequence[DbName] = (DbName.timeseries,),
    repo_factories: Optional[Dict[DbName, RepoFactory]] = None,
) -> None:
    reg = await build_timeseries_registry(dbs=dbs, repo_factories=repo_factories)

    # Expose les mêmes attributs qu'avant pour compatibilité
    app.state.timeseries_map = reg.timeseries_map
    app.state.timeseries_by_id = reg.timeseries_by_id
    app.state.timeseries_by_provider = reg.timeseries_by_provider
    app.state.timeseries_map_date = reg.timeseries_map_date

    # Bonus utile : exposer l’objet complet
    app.state.timeseries_registry = reg
