DROP TABLE IF EXISTS route_points;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS gear_items;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS route_photos;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,          -- '' для аккаунтов, созданных через Google
    email         TEXT,
    google_sub    TEXT UNIQUE,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_users_username_nocase ON users(username COLLATE NOCASE);

CREATE TABLE routes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id      INTEGER NOT NULL REFERENCES users(id),
    title          TEXT NOT NULL,
    region         TEXT NOT NULL,
    length_km      REAL NOT NULL,
    difficulty     TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    days           INTEGER NOT NULL DEFAULT 1,
    season         TEXT NOT NULL DEFAULT 'any',
    terrain        TEXT NOT NULL DEFAULT 'any',
    description    TEXT NOT NULL,
    restrictions   TEXT,
    source_url     TEXT,
    source_checked TEXT,
    open_from      TEXT,
    open_to        TEXT,
    is_public      INTEGER NOT NULL DEFAULT 1,
    views          INTEGER NOT NULL DEFAULT 0,
    surface        TEXT,
    max_slope      TEXT,
    has_steps      INTEGER NOT NULL DEFAULT 0,
    rest_points    TEXT,
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE route_points (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    kind     TEXT NOT NULL DEFAULT 'path' CHECK (kind IN ('path', 'place')),
    lat      REAL NOT NULL,
    lon      REAL NOT NULL,
    name     TEXT,
    note     TEXT
);

CREATE TABLE route_photos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id   INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    filename   TEXT NOT NULL,
    caption    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_photos_route ON route_photos(route_id);

CREATE TABLE gear_items (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    category TEXT NOT NULL,
    season   TEXT NOT NULL DEFAULT 'any',
    terrain  TEXT NOT NULL DEFAULT 'any',
    min_days INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_routes_region     ON routes(region);
CREATE INDEX idx_routes_difficulty ON routes(difficulty);
CREATE INDEX idx_routes_length     ON routes(length_km);
CREATE INDEX idx_points_route      ON route_points(route_id);