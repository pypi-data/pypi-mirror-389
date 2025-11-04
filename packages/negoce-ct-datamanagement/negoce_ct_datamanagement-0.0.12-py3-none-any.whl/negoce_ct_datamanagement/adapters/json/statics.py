from __future__ import annotations

from decimal import Decimal
from typing import Iterable, List, Dict, Any

from negoce_ct_datamanagement.models.statics import (
    ExpectedFlowIn,
    FlowPowerConversionIn,
    SeujetEvacuationCapacityIn,
    LemanLevelIn,
)


# ------------------ JSON → domain helpers ------------------

# Each function accepts either a dict (single item) or a list[dict] (batch)
# and returns the corresponding domain instances. Minimal validation included.


def expected_flows_from_json(payload: Any) -> List[ExpectedFlowIn]:
    items = _ensure_list(payload)
    out: List[ExpectedFlowIn] = []
    for it in items:
        out.append(
            ExpectedFlowIn(
                dam_id=int(it["dam_id"]),
                inflow=int(it["inflow"]),
                expected_flow=int(it["expected_flow"]),
            )
        )
    return out


def flow_power_from_json(payload: Any) -> List[FlowPowerConversionIn]:
    items = _ensure_list(payload)
    out: List[FlowPowerConversionIn] = []
    for it in items:
        out.append(
            FlowPowerConversionIn(
                dam_id=int(it["dam_id"]),
                flow=int(it["flow"]),
                group_no=int(it["group_no"]),
                power_mw=Decimal(str(it["power_mw"])) ,
                leman_level=Decimal(str(it["leman_level"])) ,
            )
        )
    return out


def seujet_capacities_from_json(payload: Any) -> List[SeujetEvacuationCapacityIn]:
    items = _ensure_list(payload)
    out: List[SeujetEvacuationCapacityIn] = []
    for it in items:
        out.append(
            SeujetEvacuationCapacityIn(
                seujet_evacuation_flow=int(it["seujet_evacuation_flow"]),
                arve_flow=int(it["arve_flow"]),
                leman_level=Decimal(str(it["leman_level"])) ,
            )
        )
    return out


def leman_levels_from_json(payload: Any) -> List[LemanLevelIn]:
    items = _ensure_list(payload)
    out: List[LemanLevelIn] = []
    for it in items:
        out.append(
            LemanLevelIn(
                leap_year=bool(it["leap_year"]),
                month=int(it["month"]),
                day=int(it["day"]),
                min_arve_call_level=_optional_decimal(it, "min_arve_call_level"),
                max_arve_call_level=_optional_decimal(it, "max_arve_call_level"),
                min_regulation_domain=_optional_decimal(it, "min_regulation_domain"),
                max_regulation_domain=_optional_decimal(it, "max_regulation_domain"),
            )
        )
    return out


# ------------------ Utils ------------------

def _ensure_list(payload: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return payload
    raise TypeError("Expected a dict or list[dict] payload")


def _optional_decimal(d: Dict[str, Any], key: str):
    if key not in d or d[key] is None:
        return None
    return Decimal(str(d[key]))
