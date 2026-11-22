"""Вход, регистрация, выход и вход через Google."""
import functools
import re
import secrets
import sqlite3

from authlib.integrations.base_client.errors import OAuthError
from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from extensions import limiter, oauth

bp = Blueprint("auth", __name__, url_prefix="/auth")

USERNAME_RE = re.compile(r"^[\w.\-]{3,32}$")
COMMON_PASSWORDS = {
    "password", "password1", "password123", "1234567890", "0123456789", "qwertyuiop",
    "qwerty123456", "1q2w3e4r5t", "1111111111", "йцукенгшщз", "iloveyou123", "admin12345",
}
# для выравнивания времени ответа, когда пользователя не существует
DUMMY_HASH = generate_password_hash("timing-dummy-password")


# ---------- Вспомогательные функции ----------

def validate_password(password, username):
    """Возвращает текст ошибки или None, если пароль подходит."""
    if len(password) < 10:
        return "Пароль должен быть не короче 10 символов."
    if len(password) > 128:
        return "Пароль слишком длинный (максимум 128 символов)."
    if password.lower() in COMMON_PASSWORDS or len(set(password)) < 4:
        return "Этот пароль слишком простой."
    if password.lower() == username.lower():
        return "Пароль не должен совпадать с именем."
    return None


def safe_next(target):
    """Разрешаем только переходы внутри сайта (защита от open redirect)."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return None


def google_enabled():
    """Заданы ли ключи Google в настройках."""
    return bool(current_app.config.get("GOOGLE_CLIENT_ID") and current_app.config.get("GOOGLE_CLIENT_SECRET"))


def start_session(user_id):
    """Начинает сессию пользователя (14 дней, см. PERMANENT_SESSION_LIFETIME)."""
    session.clear()  # против session fixation
    session["user_id"] = user_id
    session.permanent = True


# ---------- Регистрация, вход и выход ----------

@bp.route("/register", methods=("GET", "POST"))
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if g.user:
        return redirect(url_for("pages.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("password2", "")
        error = None

        if not USERNAME_RE.match(username):
            error = "Имя: 3–32 символа, только буквы, цифры, точка, дефис и подчёркивание."
        elif password != confirm:
            error = "Пароли не совпадают."
        else:
            error = validate_password(password, username)

        if error is None:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except sqlite3.IntegrityError:
                error = "Такое имя уже занято."
            else:
                start_session(cur.lastrowid)
                return redirect(url_for("pages.index"))

        flash(error)
    return render_template("register.html")


@bp.route("/login", methods=("GET", "POST"))
@limiter.limit("10 per minute;60 per hour", methods=["POST"])
def login():
    if g.user:
        return redirect(url_for("pages.index"))
    nxt = safe_next(request.values.get("next"))  # куда вернуть после входа
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
        ).fetchone()

        # Хеш проверяем всегда (даже для несуществующего пользователя), чтобы по времени
        # ответа нельзя было угадать, есть ли такое имя. У Google-аккаунтов хеш пустой.
        stored = user["password_hash"] if user else ""
        ok = check_password_hash(stored or DUMMY_HASH, password[:128])
        if user is None or not stored or not ok:
            flash("Неверное имя или пароль.")
        else:
            start_session(user["id"])
            return redirect(nxt or url_for("pages.index"))
    return render_template("login.html", next=nxt)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("pages.index"))


# ---------- Вход через Google (OpenID Connect) ----------

@bp.route("/google")
@limiter.limit("20 per minute")
def google_login():
    """Отправляет пользователя на страницу входа Google."""
    if not google_enabled():
        flash("Вход через Google не настроен.")
        return redirect(url_for("auth.login"))
    session["oauth_next"] = safe_next(request.args.get("next")) or ""
    return oauth.google.authorize_redirect(url_for("auth.google_callback", _external=True))


def _unique_username(db, name):
    """Подбирает свободное имя пользователя на основе имени из Google."""
    base = re.sub(r"[^\w.\-]", "", name or "")[:24] or "user"
    if len(base) < 3:
        base = base + "_user"
    candidate = base
    for _ in range(10):
        if not db.execute("SELECT 1 FROM users WHERE username = ? COLLATE NOCASE", (candidate,)).fetchone():
            return candidate
        candidate = f"{base}{secrets.randbelow(9000) + 1000}"  # имя занято: добавляем число
    return f"user{secrets.token_hex(4)}"


@bp.route("/google/callback")
def google_callback():
    """Google возвращает пользователя сюда: проверяем ответ, находим или создаём аккаунт."""
    if not google_enabled():
        return redirect(url_for("auth.login"))
    try:
        token = oauth.google.authorize_access_token()  # проверяет state и подпись id_token
    except OAuthError:
        flash("Не удалось войти через Google. Попробуйте ещё раз.")
        return redirect(url_for("auth.login"))

    info = token.get("userinfo") or {}
    sub, email = info.get("sub"), info.get("email")  # sub — постоянный id пользователя в Google
    if not sub or not email or not info.get("email_verified"):
        flash("Google не подтвердил адрес почты, вход невозможен.")
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE google_sub = ?", (sub,)).fetchone()
    if user is None:
        # Первый вход через Google: создаём аккаунт (несколько попыток на случай гонки имён)
        name = info.get("name") or email.split("@")[0]
        for _ in range(3):
            try:
                cur = db.execute(
                    "INSERT INTO users (username, password_hash, email, google_sub) VALUES (?, '', ?, ?)",
                    (_unique_username(db, name), email, sub),
                )
                db.commit()
                user_id = cur.lastrowid
                break
            except sqlite3.IntegrityError:
                db.rollback()
        else:
            flash("Не удалось создать аккаунт. Попробуйте ещё раз.")
            return redirect(url_for("auth.login"))
    else:
        user_id = user["id"]

    nxt = safe_next(session.get("oauth_next"))
    start_session(user_id)
    return redirect(nxt or url_for("pages.index"))


# ---------- Текущий пользователь и защита страниц ----------

@bp.before_app_request
def load_logged_in_user():
    """Перед каждым запросом кладёт текущего пользователя в g.user (или None)."""
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if g.user is None:
            session.clear()  # пользователя уже нет в базе


def login_required(view):
    """Декоратор: неавторизованных отправляет на вход и запоминает, куда вернуть."""
    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.user is None:
            nxt = request.full_path.rstrip("?") if request.method == "GET" else None
            return redirect(url_for("auth.login", next=nxt))
        return view(**kwargs)
    return wrapped
