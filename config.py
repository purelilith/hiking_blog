import os
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _load_secret_key():
    """SECRET_KEY из окружения; если нет — генерируем один раз и храним в файле (вне git)."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    import secrets
    path = os.path.join(BASE_DIR, ".secret_key")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as f:
        f.write(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


SECRET_KEY = _load_secret_key()
DATABASE = os.path.join(BASE_DIR, "hiking.db")

# Cookie сессии
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE") == "1"
PERMANENT_SESSION_LIFETIME = timedelta(days=14)

# CSRF-токен живёт столько же, сколько сессия
WTF_CSRF_TIME_LIMIT = None

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")