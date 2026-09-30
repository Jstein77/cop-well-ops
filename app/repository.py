import sqlite3
from typing import Any

from app.db import fetch_all, fetch_one


def list_wells(conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status:
        return fetch_all(conn, "SELECT * FROM wells WHERE status = ? ORDER BY name", (status,))
    return fetch_all(conn, "SELECT * FROM wells ORDER BY name")


def get_well(conn: sqlite3.Connection, well_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM wells WHERE id = ?", (well_id,))


def list_shift_log(
    conn: sqlite3.Connection, well_id: int | None = None, limit: int = 20
) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT shift_log.*, wells.name AS well_name FROM shift_log"
        " JOIN wells ON wells.id = shift_log.well_id"
        " WHERE (? IS NULL OR shift_log.well_id = ?)"
        " ORDER BY logged_at DESC LIMIT ?",
        (well_id, well_id, limit),
    )
