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
    db.commit()


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("База создана.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)