from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass(frozen=True)
class Dam:
    id: int
    name: str

@dataclass(frozen=True)
class DamIn:
    name: str

@dataclass(frozen=True)
class ExpectedFlow:
    dam_id: int
    inflow: int
    expected_flow: int

@dataclass(frozen=True)
class ExpectedFlowIn:
    dam_id: int
    inflow: int
    expected_flow: int

@dataclass(frozen=True)
class SeujetEvacuationCapacity:
    seujet_evacuation_flow: int
    arve_flow: int
    leman_level: Decimal

@dataclass(frozen=True)
class SeujetEvacuationCapacityIn:
    seujet_evacuation_flow: int
    arve_flow: int
    leman_level: Decimal

@dataclass(frozen=True)
class FlowPowerConversion:
    id: int
    dam_id: int
    flow: int
    group_no: int
    power_mw: Decimal
    leman_level: Decimal

@dataclass(frozen=True)
class FlowPowerConversionIn:
    dam_id: int
    flow: int
    group_no: int
    power_mw: Decimal
    leman_level: Decimal

@dataclass(frozen=True)
class LemanLevel:
    leap_year: bool
    month: int
    day: int
    min_arve_call_level: Optional[Decimal]
    max_arve_call_level: Optional[Decimal]
    min_regulation_domain: Optional[Decimal]
    max_regulation_domain: Optional[Decimal]

@dataclass(frozen=True)
class LemanLevelIn:
    leap_year: bool
    month: int
    day: int
    min_arve_call_level: Optional[Decimal] = None
    max_arve_call_level: Optional[Decimal] = None
    min_regulation_domain: Optional[Decimal] = None
    max_regulation_domain: Optional[Decimal] = None
