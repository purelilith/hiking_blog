import sqlite3
import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))


def ensure_schema():
    """Мягкая миграция users под Google-вход; данные не трогает."""
    db = get_db()
    cols = {r["name"] for r in db.execute("PRAGMA table_info(users)")}
    if not cols:
        return  # база ещё не создана (flask init-db)
    if "email" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "google_sub" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub)")
    try:
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_nocase "
                   "ON users(username COLLATE NOCASE)")
    except sqlite3.IntegrityError:
        pass  # в старой базе есть имена, различающиеся только регистром
    pcols = {r["name"] for r in db.execute("PRAGMA table_info(route_points)")}
    if "kind" not in pcols:
        db.execute("ALTER TABLE route_points ADD COLUMN kind TEXT NOT NULL DEFAULT 'path'")
    if "name" not in pcols:
        db.execute("ALTER TABLE route_points ADD COLUMN name TEXT")
    db.execute("""CREATE TABLE IF NOT EXISTS route_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(id),
        filename TEXT NOT NULL,
        caption TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_photos_route ON route_photos(route_id)")
    rcols = {r["name"] for r in db.execute("PRAGMA table_info(routes)")}
    if "kind" not in rcols:
        db.execute("ALTER TABLE routes ADD COLUMN kind TEXT NOT NULL DEFAULT 'community'")
    if "is_closed" not in rcols:
        db.execute("ALTER TABLE routes ADD COLUMN is_closed INTEGER NOT NULL DEFAULT 0")
    db.commit()


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("База создана.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)