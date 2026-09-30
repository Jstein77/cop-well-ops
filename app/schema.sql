CREATE TABLE IF NOT EXISTS wells (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    pad TEXT NOT NULL,
    field_area TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('producing', 'shut_in', 'workover', 'drilling')),
    oil_bopd REAL NOT NULL DEFAULT 0,
    gas_mcfd REAL NOT NULL DEFAULT 0,
    water_cut_pct REAL NOT NULL DEFAULT 0,
    last_inspection DATE NOT NULL
);
