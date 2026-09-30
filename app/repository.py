import sqlite3
from typing import Any

from app.db import fetch_all, fetch_one


def list_wells(conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status:
        return fetch_all(conn, "SELECT * FROM wells WHERE status = ? ORDER BY name", (status,))
    return fetch_all(conn, "SELECT * FROM wells ORDER BY name")


def get_well(conn: sqlite3.Connection, well_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM wells WHERE id = ?", (well_id,))
