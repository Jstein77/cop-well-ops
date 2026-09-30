from datetime import date
from typing import Literal

from pydantic import BaseModel

WellStatus = Literal["producing", "shut_in", "workover", "drilling"]


class Well(BaseModel):
    id: int
    name: str
    pad: str
    field_area: str
    status: WellStatus
    lift_type: str
    oil_bopd: float
    target_oil_bopd: float
    gas_mcfd: float
    water_cut_pct: float
    last_inspection: date
    status_note: str


class Deferment(BaseModel):
    well_id: int
    well_name: str
    pad: str
    status: WellStatus
    lost_bopd: float
    cause: str
    planned: bool
    owner: str
    next_action: str
    expected_restart: date | None


class IntegrityItem(BaseModel):
    id: int
    well_id: int
    well_name: str
    check_type: str
    due_date: date
    owner: str
    state: Literal["overdue", "due"]
    days_overdue: int


class DefermentReport(BaseModel):
    as_of: date
    due_within_days: int
    total_lost_bopd: float
    deferments: list[Deferment]
    integrity: list[IntegrityItem]
