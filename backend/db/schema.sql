-- Agra / ShambaAdvisor offline schema (SQLite + FTS5)

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS crops (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    name_yo       TEXT,
    ph_min        REAL NOT NULL,
    ph_max        REAL NOT NULL,
    n_min         REAL NOT NULL,
    n_max         REAL NOT NULL,
    p_min         REAL NOT NULL,
    p_max         REAL NOT NULL,
    k_min         REAL NOT NULL,
    k_max         REAL NOT NULL,
    soil_types    TEXT NOT NULL,
    season_notes  TEXT,
    season_notes_yo TEXT
);

CREATE TABLE IF NOT EXISTS advisories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    category  TEXT NOT NULL,
    lang      TEXT NOT NULL DEFAULT 'en',
    body      TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS advisories_fts USING fts5(
    title, body, category, lang,
    content='advisories', content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS advisories_ai AFTER INSERT ON advisories BEGIN
    INSERT INTO advisories_fts(rowid, title, body, category, lang)
    VALUES (new.id, new.title, new.body, new.category, new.lang);
END;
CREATE TRIGGER IF NOT EXISTS advisories_ad AFTER DELETE ON advisories BEGIN
    INSERT INTO advisories_fts(advisories_fts, rowid, title, body, category, lang)
    VALUES('delete', old.id, old.title, old.body, old.category, old.lang);
END;
CREATE TRIGGER IF NOT EXISTS advisories_au AFTER UPDATE ON advisories BEGIN
    INSERT INTO advisories_fts(advisories_fts, rowid, title, body, category, lang)
    VALUES('delete', old.id, old.title, old.body, old.category, old.lang);
    INSERT INTO advisories_fts(rowid, title, body, category, lang)
    VALUES (new.id, new.title, new.body, new.category, new.lang);
END;

CREATE TABLE IF NOT EXISTS harvest_batches (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id      TEXT NOT NULL UNIQUE,
    farmer_name   TEXT NOT NULL,
    location      TEXT NOT NULL,
    crop_type     TEXT NOT NULL,
    harvest_date  TEXT NOT NULL,
    weight_kg     REAL NOT NULL,
    quality_grade TEXT NOT NULL,
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_batches_farmer ON harvest_batches(farmer_name);
CREATE INDEX IF NOT EXISTS idx_batches_crop ON harvest_batches(crop_type);
