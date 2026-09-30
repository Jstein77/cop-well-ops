import sqlite3

from app.db import fetch_one, init_schema

# Synthetic data only. Names, people, and events are made up and do not correspond
# to real fields, wells, or staff.
WELLS = [
    # name, pad, field area, status, lift, oil, target oil, gas, water cut, inspected, note
    ("Ptarmigan-7", "Pad A", "Tundra Ridge", "producing", "ESP",
     1840, 1900, 2210, 18.5, "2026-09-12", ""),
    ("Caribou-3", "Pad A", "Tundra Ridge", "producing", "Gas lift",
     2125, 2100, 2580, 12.0, "2026-09-03", ""),
    ("Muskox-12", "Pad A", "Tundra Ridge", "shut_in", "ESP",
     0, 1650, 0, 0, "2026-05-21",
     "ESP tripped on high motor temperature. Pump change booked with the workover rig."),
    ("Wolverine-4", "Pad B", "Tundra Ridge", "producing", "Gas lift",
     960, 1300, 1405, 34.2, "2026-08-27",
     "Rate down 26% vs target. Gas lift injection being re-optimized."),
    ("Snowgoose-9", "Pad B", "Frostline", "workover", "ESP",
     0, 1400, 0, 41.0, "2026-09-18", "Coiled tubing cleanout, day 3 of 5."),
    ("Lynx-1", "Pad B", "Frostline", "producing", "Natural flow",
     1510, 1550, 1980, 22.7, "2026-06-02", ""),
    ("Arcticfox-6", "Pad C", "Frostline", "drilling", "Not installed",
     0, 0, 0, 0, "2026-09-25", "Drilling 8-1/2 in. section at 9,850 ft MD."),
    ("Raven-11", "Pad C", "Frostline", "producing", "ESP",
     1195, 1250, 1620, 27.9, "2026-08-14", ""),
    ("Grayling-2", "Pad C", "Icefall", "producing", "Natural flow",
     2380, 2300, 3015, 9.4, "2026-09-09", ""),
    ("Sandpiper-5", "Pad D", "Icefall", "shut_in", "Gas lift",
     0, 1100, 0, 0, "2026-04-30",
     "Shut in for sustained annulus pressure. Integrity review pending."),
    ("Marten-10", "Pad D", "Icefall", "producing", "ESP",
     705, 950, 990, 46.3, "2026-07-11",
     "Water cut climbing. Candidate for water shut-off review."),
    ("Kestrel-8", "Pad D", "Icefall", "workover", "Gas lift",
     0, 1250, 0, 38.8, "2026-09-21", "Gas lift valve change-out in progress."),
]  # fmt: skip

DEFERMENTS = [
    # well name, cause, planned, owner, next action, expected restart (None = not yet known)
    ("Muskox-12", "ESP failure", 0, "R. Okafor",
     "Pump change with workover rig", "2026-10-02"),
    ("Snowgoose-9", "Coiled tubing cleanout", 1, "J. Alvarez",
     "Finish cleanout and hand back to production", "2026-10-02"),
    ("Kestrel-8", "Gas lift valve change-out", 1, "R. Okafor",
     "Slickline to set remaining two valves", "2026-10-01"),
    ("Sandpiper-5", "Sustained annulus pressure", 0, "S. Patel",
     "Integrity review of bleed-down data", None),
    ("Wolverine-4", "Gas lift under-injection", 0, "M. Chen",
     "Re-test after injection increase", "2026-10-01"),
    ("Marten-10", "High water cut", 0, "M. Chen",
     "Water shut-off candidate review", None),
    ("Ptarmigan-7", "ESP frequency reduced", 0, "S. Patel",
     "Step frequency back up after vibration check", "2026-10-01"),
]  # fmt: skip

INTEGRITY_CHECKS = [
    # well name, check type, due date, owner
    ("Muskox-12", "Wellhead inspection", "2026-08-19", "R. Okafor"),
    ("Lynx-1", "Wellhead inspection", "2026-08-31", "R. Okafor"),
    ("Sandpiper-5", "Annulus pressure review", "2026-09-20", "S. Patel"),
    ("Marten-10", "Safety valve test", "2026-10-04", "M. Chen"),
    ("Caribou-3", "Safety valve test", "2026-10-09", "T. Nakamura"),
    ("Grayling-2", "Safety valve test", "2026-10-15", "J. Alvarez"),
    ("Raven-11", "Wellhead inspection", "2026-11-12", "S. Patel"),
]

SHIFT_LOG = [
    # well name, logged at, author, category, note
    ("Muskox-12", "2026-09-30T06:40", "R. Okafor", "Maintenance",
     "Rig crew confirmed for pump change Thursday. Wellhead isolated and tagged out."),
    ("Wolverine-4", "2026-09-30T05:15", "M. Chen", "Production",
     "Raised gas lift injection to 1.2 MMscf/d. Watching rate over the next two tests."),
    ("Snowgoose-9", "2026-09-30T03:50", "J. Alvarez", "Maintenance",
     "CT cleanout reached 8,200 ft. Returns clearing. On plan for Friday handback."),
    ("Arcticfox-6", "2026-09-30T02:05", "T. Nakamura", "Drilling",
     "Section TD expected tomorrow. No losses."),
    ("Sandpiper-5", "2026-09-29T18:30", "S. Patel", "Integrity",
     "Annulus B pressure 450 psi and holding. Integrity engineer reviewing bleed-down data."),
    ("Kestrel-8", "2026-09-29T16:10", "R. Okafor", "Maintenance",
     "Slickline pulled two of four gas lift valves. Resume at first light."),
    ("Marten-10", "2026-09-29T14:45", "M. Chen", "Production",
     "Well test: 705 bopd, 46% water cut. Flagged for water shut-off candidate list."),
    ("Grayling-2", "2026-09-29T09:20", "J. Alvarez", "Production",
     "Choke opened from 40 to 44. Rate up 80 bopd, sand monitor clean."),
    ("Caribou-3", "2026-09-28T21:00", "T. Nakamura", "Safety",
     "Pad A walkdown complete. No leaks found. Housekeeping item logged for flare knockout."),
    ("Ptarmigan-7", "2026-09-28T11:35", "S. Patel", "Production",
     "ESP frequency trimmed to 54 Hz after vibration alarm cleared. Rate steady."),
    ("Lynx-1", "2026-09-27T15:00", "R. Okafor", "Integrity",
     "Inspection overdue. Scheduled for next week's Pad B campaign."),
]  # fmt: skip


def seed_if_empty(conn: sqlite3.Connection) -> None:
    init_schema(conn)
    if fetch_one(conn, "SELECT COUNT(*) AS n FROM wells")["n"]:
        return
    conn.executemany(
        "INSERT INTO wells (name, pad, field_area, status, lift_type, oil_bopd, target_oil_bopd,"
        " gas_mcfd, water_cut_pct, last_inspection, status_note)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        WELLS,
    )
    conn.executemany(
        "INSERT INTO shift_log (well_id, logged_at, author, category, note)"
        " SELECT id, ?, ?, ?, ? FROM wells WHERE name = ?",
        [(logged_at, author, category, note, name) for name, logged_at, author, category, note
         in SHIFT_LOG],
    )  # fmt: skip
    conn.executemany(
        "INSERT INTO deferments (well_id, cause, planned, owner, next_action, expected_restart)"
        " SELECT id, ?, ?, ?, ?, ? FROM wells WHERE name = ?",
        [(*rest, name) for name, *rest in DEFERMENTS],
    )
    conn.executemany(
        "INSERT INTO integrity_checks (well_id, check_type, due_date, owner)"
        " SELECT id, ?, ?, ? FROM wells WHERE name = ?",
        [(*rest, name) for name, *rest in INTEGRITY_CHECKS],
    )
    conn.commit()
