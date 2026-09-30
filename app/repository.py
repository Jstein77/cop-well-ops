import sqlite3
from typing import Any

from app.db import fetch_all, fetch_one


def list_wells(
    conn: sqlite3.Connection, status: str | None = None, field_area: str | None = None
) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT * FROM wells"
        " WHERE (? IS NULL OR status = ?) AND (? IS NULL OR field_area = ?)"
        " ORDER BY name",
        (status, status, field_area, field_area),
    )


def get_well(conn: sqlite3.Connection, well_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM wells WHERE id = ?", (well_id,))


def list_field_areas(conn: sqlite3.Connection) -> list[str]:
    rows = fetch_all(conn, "SELECT DISTINCT field_area FROM wells ORDER BY field_area")
    return [row["field_area"] for row in rows]


def status_summary(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT status, COUNT(*) AS wells, SUM(oil_bopd) AS oil_bopd, SUM(gas_mcfd) AS gas_mcfd"
        " FROM wells GROUP BY status ORDER BY status",
    )
