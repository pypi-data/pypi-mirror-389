
# -*- coding: utf-8 -*-
"""
Script pour écrire un CSV de points de séries temporelles via belvis.requests_utils.

Hypothèses sur le CSV (colonnes détectées) :
  - ts : horodatage (str, ISO8601 ou 'YYYY-MM-DD HH:MM:SS'), sans fuseau => interprété en Europe/Zurich
  - v : valeur numérique
  - date_prediction : (optionnel) méta non utilisée par l'API, conservée pour info
  - timeseries_id : identifiant numérique de la série (peut varier par ligne)

Utilisation (depuis un venv où negoce_ct_datamanagement est installé) :
    python write_csv_timeseries.py /chemin/vers/forecasts_previsions.csv --pf estimated --chunk 500 --tz Europe/Zurich

"""
from __future__ import annotations
import argparse
import math
import sys
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any

import pandas as pd
from requests import HTTPError, Response
from zoneinfo import ZoneInfo
from datetime import datetime, date, time, timedelta

from pathlib import Path
import os
from dotenv import load_dotenv
TSID = 88807817
TZ = ZoneInfo("Europe/Zurich")

# Chargement des .env (identique à ton snippet)
ENV = os.getenv("ENV", "production")
# On sécurise le cas où __file__ n'a pas 3 parents dans ton layout
here = Path(__file__).resolve()
for parents_up in (3, 2, 1, 0):
    candidate = here.parents[parents_up] / f".env.{ENV}" if parents_up < len(here.parents) else None
    if candidate and candidate.exists():
        load_dotenv(str(candidate))
        break
load_dotenv()

from negoce_ct_datamanagement.providers.belvis.requests_utils import (
    write_timeseries,
    WriteOptions,
    read_timeseries,
    ReadOptions,
    read_timeseries_properties,
)
from requests import HTTPError, Response
import pandas as pd
import sys

@dataclass
class WriteConfig:
    tz: str = "Europe/Zurich"
    chunk: int = 500
    pf: str | None = "estimated"
    blocking: bool = True
    check_origin: bool = True
    allow_historical: bool = True
    mark_dependencies: bool = False
    dry_run: bool = False
    verbose: bool = True
    retries: int = 3              # nb de tentatives par chunk sur erreurs 5xx/timeout
    backoff: float = 2.0          # facteur d’attente exponentielle: 1s, 2s, 4s...
    min_chunk: int = 10           # taille minimale avant d’arrêter de splitter
    pause_between_chunks: float = 0.0  # pause entre lots (secondes)

def _coerce_ts(x, tz_name: str, nonexistent: str = "shift_forward", ambiguous="raise") -> str:
    """
    Convertit x en timestamp aware ISO8601 dans tz_name.
    - naive -> tz_localize(tz_name, nonexistent=..., ambiguous=...)
    - aware -> tz_convert(tz_name)
    Compat pandas: si ambiguous == "infer" mais non supporté, on replie sur True.
    """
    import pandas as pd

    # Normalisation des paramètres
    def _norm_amb(a):
        if a is True or a is False or a in ("NaT", "raise"):
            return a
        if isinstance(a, str):
            al = a.strip().lower()
            if al in ("true", "t", "1", "first"):
                return True
            if al in ("false", "f", "0", "second"):
                return False
            if al in ("nat", "nan"):
                return "NaT"
            if al in ("raise",):
                return "raise"
            if al in ("infer",):
                # Certaines versions de pandas ne supportent pas 'infer'
                # -> repli sûr : True (1ère occurrence)
                return True
        # défaut conservateur
        return "raise"

    amb = _norm_amb(ambiguous)
    nonexist = nonexistent  # "shift_forward" / "shift_backward" / "NaT" / "raise"

    dt = pd.to_datetime(x, utc=False, errors="raise")

    if getattr(dt, "tzinfo", None) is None:
        # localisation (naive -> aware)
        try:
            dt = dt.tz_localize(tz_name, nonexistent=nonexist, ambiguous=amb)
        except TypeError:
            # Très vieilles versions: pas de param 'nonexistent'
            # -> on réessaie sans le param et on laisse lever NonExistentTimeError si ça arrive
            dt = dt.tz_localize(tz_name, ambiguous=amb)
    else:
        # conversion (aware -> autre tz)
        dt = dt.tz_convert(tz_name)

    if pd.isna(dt):
        raise ValueError(f"Horodatage invalide/NaT après localize: {x!r}")

def build_payload(
    df: pd.DataFrame,
    tz_name: str,
    pf: str | None,
    nonexistent: str = "shift_forward",
    ambiguous="raise",
    on_bad_value: str = "drop",      # déjà ajouté précédemment
    on_bad_ts: str = "raise",        # <--- AJOUT: "raise" | "drop"
) -> Dict[int, List[Dict[str, Any]]]:

    import pandas as pd, math

    required = {"ts", "v", "timeseries_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV: {sorted(missing)}")

    work = df.copy()

    # 1) Timestamps -> ISO string aware
    work["ts"] = work["ts"].apply(
        lambda x: _parse_ts_value(x, tz_name, nonexistent=nonexistent, ambiguous=ambiguous)
    )
    bad_ts_mask = work["ts"].isna() | (work["ts"].astype(object) == None)
    bad_ts_count = int(bad_ts_mask.sum())
    if bad_ts_count:
        examples = work.loc[bad_ts_mask, ["ts", "timeseries_id"]].head(5).to_dict("records")
        if on_bad_ts == "raise":
            raise ValueError(
                f"{bad_ts_count} timestamp(s) illisible(s) -> ts=None. "
                f"Exemples (colonne 'ts' d'origine montrée telle que lue): {examples}"
            )
        # sinon on droppe les lignes sans ts
        work = work[~bad_ts_mask]

    # 2) Valeurs numériques -> float
    work["v"], bad_count, bad_examples = _clean_numeric_series(work["v"], policy=on_bad_value)

    # 3) Filtre strict des valeurs non finies
    before = len(work)
    work = work[work["v"].apply(lambda x: (x is not None) and (not pd.isna(x)) and math.isfinite(float(x)))]
    dropped_v = before - len(work)

    if on_bad_ts != "drop" and bad_ts_count:
        # sécurité redondante si on a choisi raise ci-dessus
        raise AssertionError("Incohérence: des ts invalides subsistent alors que on_bad_ts='raise'.")

    if len(work) == 0:
        raise ValueError("Aucune ligne exploitable après nettoyage (ts/v).")

    # 4) Tri stable
    work = work.sort_values(["timeseries_id", "ts"]).reset_index(drop=True)

    # 5) Construction des payloads par série
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for tsid, sub in work.groupby("timeseries_id"):
        pl = []
        for ts, v in zip(sub["ts"].tolist(), sub["v"].tolist()):
            item = {"ts": ts, "v": float(v)}
            # Toujours envoyer un pf explicite pour éviter 'missing'
            item["pf"] = "estimated" if pf is None else pf
            pl.append(item)
        grouped[int(tsid)] = pl

    # Petit récap utile
    if bad_ts_count or dropped_v:
        print(f"[CLEAN] ts supprimés: {bad_ts_count} | v supprimées: {dropped_v}")
    # garde le dernier pour chaque ts
    by_ts = {}
    for item in pl:
        by_ts[item["ts"]] = item  # ou agréger ici (mean/sum) selon besoin
    # replace with stable, trié par ts
    grouped[tsid] = sorted(by_ts.values(), key=lambda d: d["ts"])
    return grouped

def _sanitize_chunk(chunk):
    import math
    clean = []
    for d in chunk:
        ts = d.get("ts")
        if not ts or str(ts).lower() == "none":
            continue  # on jette ce point
        v = d.get("v")
        try:
            fv = float(v)
        except Exception:
            continue
        if not math.isfinite(fv):
            continue
        dd = dict(d)
        dd["ts"] = str(ts)  # s'assure que c'est une string
        dd["v"] = fv
        dd.setdefault("pf", "estimated")
        clean.append(dd)
    return clean


def write_group(tsid, points, cfg):
    """
    Envoie 'points' sur le tsid donné avec:
      - chunking (cfg.chunk)
      - retry (cfg.retries) avec backoff (cfg.backoff)
      - split automatique jusqu'à cfg.min_chunk
      - pause entre lots (cfg.pause_between_chunks)
      - logs verbeux si cfg.verbose
    """
    import time
    from requests import HTTPError
    from requests.exceptions import ConnectionError, Timeout
    from urllib3.exceptions import ProtocolError

    opts = WriteOptions(
        blocking=cfg.blocking,
        markDependencies=cfg.mark_dependencies,
        checkOrigin=cfg.check_origin,
        allowHistoricalData=cfg.allow_historical,
    )
    if cfg.verbose:
        print(
            f"Options: blocking={opts.blocking}, "
            f"checkOrigin={opts.checkOrigin}, "
            f"allowHistoricalData={opts.allowHistoricalData}, "
            f"markDependencies={opts.markDependencies}"
        )

    def send_chunk(chunk, attempt=1):
        """Envoie un chunk avec retries; split si erreurs persistantes."""
        if cfg.dry_run:
            return

        try:
            resp = write_timeseries(timeseries_id=int(tsid), data=chunk, options=WriteOptions(blocking=True, checkOrigin=False, allowHistoricalData=True))
            if cfg.verbose:
                # Log minimal du retour si disponible (Response ou objet custom)
                try:
                    from requests import Response as _Resp  # safe import
                    if isinstance(resp, _Resp):
                        status = getattr(resp, "status_code", "?")
                        reason = getattr(resp, "reason", "")
                        print(f"  -> HTTP {status} {reason}")
                    else:
                        print(f"  -> resp: {repr(resp)[:200]}")
                except Exception:
                    pass
            return  # succès

        except (ConnectionError, Timeout, ProtocolError) as e:
            # Erreurs réseau -> retry puis split si nécessaire
            if cfg.verbose:
                print(f"  -> Réseau: {e.__class__.__name__} (tentative {attempt}/{cfg.retries})")
            if attempt < cfg.retries:
                sleep_s = cfg.backoff ** (attempt - 1)
                if cfg.verbose:
                    print(f"     Attente {sleep_s:.2f}s puis retry…")
                time.sleep(sleep_s)
                return send_chunk(chunk, attempt + 1)
            # plus de retries: on essaye de splitter
            if len(chunk) > getattr(cfg, "min_chunk", 10):
                mid = max(1, len(chunk) // 2)
                if cfg.verbose:
                    print(f"  -> Split du lot ({len(chunk)} → {mid} + {len(chunk)-mid})")
                send_chunk(chunk[:mid], attempt=1)
                send_chunk(chunk[mid:], attempt=1)
                return
            # taille minimale atteinte: on remonte
            raise

        except HTTPError as e:
            r = getattr(e, "response", None)
            status = getattr(r, "status_code", None)
            body = getattr(r, "text", "")
            print(f"  -> HTTPError {status}. Body: {body[:800]}")
            # 429/5xx => retry puis split
            if status in (429, 500, 502, 503, 504):
                if attempt < cfg.retries:
                    sleep_s = cfg.backoff ** (attempt - 1)
                    # Respecte Retry-After si présent
                    try:
                        ra = getattr(r, "headers", {}).get("Retry-After")
                        if ra:
                            sleep_s = float(ra)
                    except Exception:
                        pass
                    if cfg.verbose:
                        print(f"     Attente {sleep_s:.2f}s puis retry…")
                    time.sleep(sleep_s)
                    return send_chunk(chunk, attempt + 1)
                # split si possible
                if len(chunk) > getattr(cfg, "min_chunk", 10):
                    mid = max(1, len(chunk) // 2)
                    if cfg.verbose:
                        print(f"  -> Split du lot ({len(chunk)} → {mid} + {len(chunk)-mid})")
                    send_chunk(chunk[:mid], attempt=1)
                    send_chunk(chunk[mid:], attempt=1)
                    return
            # autres HTTP ou plus de split possible -> remonte
            raise

    total = len(points)
    i = 0
    def _dedup_chunk(chunk):
        seen = {}
        for d in chunk:
            seen[d["ts"]] = d   # dernier gagne
        return list(seen.values())
    while i < total:
        end = min(i + cfg.chunk, total)
        raw_chunk = points[i:end]

        # Nettoyage du lot
        chunk = _sanitize_chunk(raw_chunk)
        chunk = _dedup_chunk(chunk)  # déduplication par ts
        if not chunk:
            if cfg.verbose:
                print(f"[WRITE] tsid={tsid} [{i+1}-{end}/{total}] -> chunk vide (toutes valeurs invalides), skip.")
            i = end
            continue

        if cfg.verbose:
            print(f"[WRITE] tsid={tsid} [{i+1}-{end}/{total}]")
            # échantillon de debug
            sample = chunk[:3]
            print("  -> sample payload:", sample)

        # Envoi + retry/split
        send_chunk(chunk, attempt=1)

        # éventuelle pause entre lots
        if getattr(cfg, "pause_between_chunks", 0.0) > 0:
            time.sleep(cfg.pause_between_chunks)

        i = end

def _clean_numeric_series(raw, policy: str = "raise"):
    """
    Nettoie une série de nombres sous forme de chaînes puis convertit en float.
    - Remplace les virgules par des points (décimales européennes)
    - Supprime les espaces (y compris insécables)
    - Supprime tout caractère non autorisé (garde 0-9, +, -, ., e, E)
    - Convertit via pd.to_numeric(errors='coerce')
    policy:
      - "raise": lève une erreur si des valeurs restent NaN
      - "drop": garde en NaN (elles seront filtrées plus loin)
      - "coerce": identique à "drop" ici (compat alias)
    Retourne: (series_float, nb_nans, exemples)
    """
    import pandas as pd
    s = raw.astype(str)

    # normalisations simples
    s = s.str.replace(",", ".", regex=False)
    s = s.str.replace(r"\s+", "", regex=True)  # supprime espaces

    # ne garde que les caractères numériques pertinents
    s = s.str.replace(r"[^0-9+\-Ee\.]", "", regex=True)

    out = pd.to_numeric(s, errors="coerce")
    bad_mask = out.isna()
    bad_count = int(bad_mask.sum())
    examples = raw[bad_mask].head(5).tolist()

    if bad_count and policy == "raise":
        raise ValueError(
            f"{bad_count} valeur(s) 'v' illisible(s) après nettoyage. "
            f"Exemples: {examples}"
        )
    return out, bad_count, examples

def _normalize_dst_params(nonexistent, ambiguous):
    """
    Normalise les paramètres DST pour pandas.tz_localize :
      - nonexistent: "shift_forward" | "shift_backward" | "NaT" | "raise"
      - ambiguous  : True | False | "NaT" | "raise" | "infer" (repli -> True)
    Retourne: (nonexist_norm, ambiguous_norm)
    """
    # nonexistent: laisser passer tel quel (pandas récents), sinon on gèrera via except TypeError
    ne = str(nonexistent) if isinstance(nonexistent, str) else nonexistent

    # ambiguous: accepter plusieurs formes textuelles
    a = ambiguous
    if isinstance(a, str):
        al = a.strip().lower()
        if al in ("true", "t", "1", "first"):
            a = True
        elif al in ("false", "f", "0", "second"):
            a = False
        elif al == "nat":
            a = "NaT"
        elif al == "raise":
            a = "raise"
        elif al == "infer":
            # certaines versions de pandas ne supportent pas 'infer' -> repli sur True
            a = True
        else:
            a = "raise"
    elif a not in (True, False, "NaT", "raise"):
        a = "raise"

    return ne, a

def _parse_ts_value(x, tz_name: str, nonexistent="shift_forward", ambiguous="raise"):
    """
    Parse un timestamp arbitraire et renvoie une string ISO 8601 aware.
    Retourne None si parsing impossible (on décidera ensuite: drop/raise).
    """
    import pandas as pd
    s = ("" if x is None else str(x)).strip()
    if not s:
        return None

    # Essais de formats (rapides -> permissif)
    for kwargs in (
        {"errors": "raise", "utc": False},                         # libre
        {"errors": "raise", "utc": False, "dayfirst": True},       # DD/MM/...
    ):
        try:
            dt = pd.to_datetime(s, **kwargs)
            break
        except Exception:
            dt = None
    if dt is None:
        return None

    try:
        ne, amb = _normalize_dst_params(nonexistent, ambiguous)
        if getattr(dt, "tzinfo", None) is None:
            try:
                dt = dt.tz_localize(tz_name, nonexistent=ne, ambiguous=amb)
            except TypeError:
                # pandas anciens : param 'nonexistent' non supporté
                dt = dt.tz_localize(tz_name, ambiguous=amb)
        else:
            dt = dt.tz_convert(tz_name)
    except Exception:
        return None

    dt = _snap_to_hour(dt, globals().get("_SNAP_MODE", "hour-start"))
    dt = dt.replace(minute=0, second=0, microsecond=0, nanosecond=0)  # sécurité
    return dt.isoformat()

def _snap_to_hour(dt, mode: str):
    # dt est un pandas.Timestamp tz-aware
    if mode == "hour-start":
        return dt.floor("H")               # 02:59:59.999 -> 02:00:00
    if mode == "hour-next":
        return dt.ceil("H")                # 02:59:59.999 -> 03:00:00
    return dt


def main(argv: list[str] | None = None) -> int:
    props = read_timeseries_properties(88807817)
    print(props)
    p = argparse.ArgumentParser(description="Écrit un CSV de points dans Belvis.")
    p.add_argument("csv_path", type=str, help="Chemin du CSV à écrire")
    p.add_argument("--tz", default="Europe/Zurich", help="Fuseau à appliquer si ts sans tz")
    p.add_argument("--pf", default="estimated", help="Production flag à appliquer (ou --pf none pour ne pas l'envoyer)")
    p.add_argument("--chunk", type=int, default=500, help="Taille de lot pour l'écriture")
    p.add_argument("--no-blocking", action="store_true", help="Ne pas bloquer côté API")
    p.add_argument("--no-check-origin", action="store_true", help="Ne pas vérifier l'origine")
    p.add_argument("--no-allow-historical", action="store_true", help="Interdire l'historique")
    p.add_argument("--mark-dependencies", action="store_true", help="Activer markDependencies")
    p.add_argument("--dry-run", action="store_true", help="Ne fait qu'afficher sans écrire")
    p.add_argument("--silent", action="store_true", help="Moins de logs")
    p.add_argument(
        "--dst-nonexistent",
        default="shift_forward",
        choices=["shift_forward", "shift_backward", "NaT", "raise"],
        help="Politique pour heures inexistantes (printemps)"
    )
    p.add_argument(
        "--dst-ambiguous",
        default="true",  # défaut robuste pour pandas anciens
        choices=["true", "false", "NaT", "raise", "infer"],  # 'infer' sera replié côté code
        help="Politique pour heures ambiguës (automne)"
    )
    p.add_argument(
        "--on-bad-value",
        default="drop",
        choices=["raise", "drop", "coerce"],
        help="Que faire des valeurs 'v' illisibles après nettoyage (défaut: drop)"
    )
    p.add_argument(
        "--require-no-drop",
        action="store_true",
        help="Échoue si des lignes 'v' invalides ont été supprimées"
    )
    p.add_argument(
        "--on-bad-ts",
        default="raise",
        choices=["raise", "drop"],
        help="Que faire des timestamps illisibles (défaut: raise)"
    )
    p.add_argument(
        "--snap-to",
        default="hour-start",  # ou "hour-next" si tes ts sont des fins d’heure
        choices=["none", "hour-start", "hour-next"],
        help="Ajuste les timestamps: 'hour-start' = hh:00:00 ; 'hour-next' = prochaine heure pile"
    )

    args = p.parse_args(argv)
    global _SNAP_MODE
    _SNAP_MODE = args.snap_to
    cfg = WriteConfig(
        tz=args.tz,
        chunk=args.chunk,
        pf=None if (args.pf is None or str(args.pf).lower() == "none") else args.pf,
        blocking=not args.no_blocking,
        check_origin=not args.no_check_origin,
        allow_historical=not args.no_allow_historical,
        mark_dependencies=args.mark_dependencies,
        dry_run=args.dry_run,
        verbose=not args.silent,
    )

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"Fichier introuvable: {csv_path}", file=sys.stderr)
        return 2

    df = pd.read_csv(csv_path)
    amb = True if args.dst_ambiguous.lower() == "true" else False if args.dst_ambiguous.lower() == "false" else args.dst_ambiguous
    grouped = build_payload(
        df, cfg.tz, cfg.pf,
        nonexistent=args.dst_nonexistent,
        ambiguous=amb,                   
        on_bad_value=args.on_bad_value,
        on_bad_ts=args.on_bad_ts,
    )
    print(f"save grouped in file")
    Path("grouped_payload.json").write_text(str(grouped))
    # payload = [{"ts":"2025-01-01T01:00:00+01:00","v":1.21,"pf":"estimated"}]
    # write_timeseries(88807817, payload, options=WriteOptions(blocking=True, checkOrigin=False, allowHistoricalData=True))
    # df = read_timeseries( TSID, date_from= datetime(2025, 1, 1, 0, 0, 0, tzinfo=TZ), date_to= datetime(2025, 1, 2, 0, 0, 0, tzinfo=TZ), options=ReadOptions(blocking=False, precision=3, Embed=False))
    # print(df)
    # total_points = sum(len(v) for v in grouped.values())
    # print(f"Prêt à écrire {total_points} points sur {len(grouped)} timeseries_id(s). dry_run={cfg.dry_run}")
    # for tsid, points in grouped.items():
    #     write_group(tsid, points, cfg)

    # print("Terminé.")
    # t = datetime.combine(date.today() + timedelta(days=1), time(12, 0, 0), tzinfo=TZ)

    date_from = datetime(2025, 11, 24, 0, 0, 0, tzinfo=TZ)
    date_to = datetime(2025, 11, 25, 0, 0, 0, tzinfo=TZ)

    df = read_timeseries(
        TSID,
        date_from=date_from,
        date_to=date_to,
        options=ReadOptions(blocking=False, precision=3, Embed=False)  # options raisonnables
    )

    print(df)   
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
#python3 negoce_ct_datamanagement/providers/belvis/uic2.py   /home/bernardsig/prevision_uic/forecasts_previsions.csv   --dst-nonexistent shift_forward --dst-ambiguous true   --on-bad-value drop --on-bad-ts raise   --chunk 10 --no-check-origin --snap-to hour-next