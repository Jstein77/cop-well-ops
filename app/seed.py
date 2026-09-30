import sqlite3

from app.db import fetch_one, init_schema

# Synthetic data only. Names are made up and do not correspond to real fields or wells.
WELLS = [
    ("Ptarmigan-7", "Pad A", "Tundra Ridge", "producing", 1840, 2210, 18.5, "2026-09-12"),
    ("Caribou-3", "Pad A", "Tundra Ridge", "producing", 2125, 2580, 12.0, "2026-09-03"),
    ("Muskox-12", "Pad A", "Tundra Ridge", "shut_in", 0, 0, 0, "2026-05-21"),
    ("Wolverine-4", "Pad B", "Tundra Ridge", "producing", 960, 1405, 34.2, "2026-08-27"),
    ("Snowgoose-9", "Pad B", "Frostline", "workover", 0, 0, 41.0, "2026-09-18"),
    ("Lynx-1", "Pad B", "Frostline", "producing", 1510, 1980, 22.7, "2026-06-02"),
    ("Arcticfox-6", "Pad C", "Frostline", "drilling", 0, 0, 0, "2026-09-25"),
    ("Raven-11", "Pad C", "Frostline", "producing", 1195, 1620, 27.9, "2026-08-14"),
    ("Grayling-2", "Pad C", "Icefall", "producing", 2380, 3015, 9.4, "2026-09-09"),
    ("Sandpiper-5", "Pad D", "Icefall", "shut_in", 0, 0, 0, "2026-04-30"),
    ("Marten-10", "Pad D", "Icefall", "producing", 705, 990, 46.3, "2026-07-11"),
    ("Kestrel-8", "Pad D", "Icefall", "workover", 0, 0, 38.8, "2026-09-21"),
]


def seed_if_empty(conn: sqlite3.Connection) -> None:
    init_schema(conn)
    if fetch_one(conn, "SELECT COUNT(*) AS n FROM wells")["n"]:
        return
    conn.executemany(
        "INSERT INTO wells (name, pad, field_area, status, oil_bopd, gas_mcfd, water_cut_pct,"
        " last_inspection) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        WELLS,
    )
    conn.commit()
