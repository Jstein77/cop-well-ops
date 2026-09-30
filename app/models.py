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
