CREATE TABLE IF NOT EXISTS wells (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    pad TEXT NOT NULL,
    field_area TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('producing', 'shut_in', 'workover', 'drilling')),
    lift_type TEXT NOT NULL,
    oil_bopd REAL NOT NULL DEFAULT 0,
    target_oil_bopd REAL NOT NULL DEFAULT 0,
    gas_mcfd REAL NOT NULL DEFAULT 0,
    water_cut_pct REAL NOT NULL DEFAULT 0,
    last_inspection DATE NOT NULL,
    status_note TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS deferments (
    id INTEGER PRIMARY KEY,
    well_id INTEGER NOT NULL UNIQUE REFERENCES wells (id),
    cause TEXT NOT NULL,
    planned INTEGER NOT NULL CHECK (planned IN (0, 1)),
    owner TEXT NOT NULL,
    next_action TEXT NOT NULL,
    expected_restart DATE
);

CREATE TABLE IF NOT EXISTS integrity_checks (
    id INTEGER PRIMARY KEY,
    well_id INTEGER NOT NULL REFERENCES wells (id),
    check_type TEXT NOT NULL,
    due_date DATE NOT NULL,
    owner TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shift_log (
    id INTEGER PRIMARY KEY,
    well_id INTEGER NOT NULL REFERENCES wells (id),
    logged_at TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT NOT NULL,
    note TEXT NOT NULL
);
