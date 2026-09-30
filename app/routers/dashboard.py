import sqlite3
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app import repository
from app.auth import User, require_reader
from app.db import get_db
from app.logging_config import get_logger
from app.models import WellStatus
from app.templating import templates

router = APIRouter(tags=["dashboard"])
logger = get_logger(__name__)

INSPECTION_INTERVAL_DAYS = 90
STATUSES = ["producing", "shut_in", "workover", "drilling"]


def inspection_overdue(last_inspection: str, today: date) -> bool:
    return (today - date.fromisoformat(last_inspection)).days > INSPECTION_INTERVAL_DAYS


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    status: WellStatus | Literal[""] | None = None,
    field_area: str | None = None,
    user: User = Depends(require_reader),
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    # The filter form submits "" for "All".
    status = status or None
    field_area = field_area or None
    today = date.today()
    wells = repository.list_wells(conn, status, field_area)
    for well in wells:
        well["overdue"] = inspection_overdue(well["last_inspection"], today)
    summary = repository.status_summary(conn)
    logger.info(
        "dashboard.view",
        extra={
            "user": user.email,
            "status": status,
            "field_area": field_area,
            "count": len(wells),
        },
    )
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "wells": wells,
            "summary": summary,
            "total_oil": sum(row["oil_bopd"] for row in summary),
            "total_gas": sum(row["gas_mcfd"] for row in summary),
            "overdue_count": sum(well["overdue"] for well in wells),
            "statuses": STATUSES,
            "field_areas": repository.list_field_areas(conn),
            "selected_status": status,
            "selected_field_area": field_area,
            "interval_days": INSPECTION_INTERVAL_DAYS,
        },
    )
