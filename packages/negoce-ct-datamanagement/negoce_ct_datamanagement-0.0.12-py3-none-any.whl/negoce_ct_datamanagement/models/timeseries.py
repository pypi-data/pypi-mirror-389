from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class SeriesIn(BaseModel):
    name: str
    domain_id: Optional[int] = None
    type_id: Optional[int] = None
    provider_id: Optional[int] = None
    area_id: Optional[int] = None
    unit_id: Optional[int] = None
    frequency_id: Optional[int] = None
    description: Optional[str] = None


class Series(BaseModel):
    id: int
    name: str
    domain_id: Optional[int] = None
    type_id: Optional[int] = None
    provider_id: Optional[int] = None
    area_id: Optional[int] = None
    unit_id: Optional[int] = None
    frequency_id: Optional[int] = None
    description: Optional[str] = None

class SeriesRef(BaseModel):
    id: int
    name: str
    type: str
    provider: str
    domain: str
    area: str
    unit: str
    frequency: str
    description: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    historical_start: Optional[datetime] = None


class PointIn(BaseModel):
    target_time: datetime
    value: float
    issue_time: Optional[datetime] = None  # None => DB mettra NOW()


class Point(BaseModel):
    series_id: int
    target_time: datetime
    value: float
    issue_time: datetime


class LoadWindowIn(BaseModel):
    name: str
    area_id: int
    dow: list[int] = Field(description="0=dim, 1=lun, ... 6=sam")
    start_time: str
    end_time: str
    include_holidays: bool = True
    timezone: str = "Europe/Zurich"


class LoadWindow(LoadWindowIn):
    id: int
