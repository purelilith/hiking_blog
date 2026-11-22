import json
import math
import os
import re
import secrets
from datetime import date

from flask import (Blueprint, abort, current_app, flash, g, jsonify, redirect,
                   render_template, request, url_for)
from markupsafe import Markup, escape
from werkzeug.utils import secure_filename

from db import get_db
from extensions import limiter
from views.auth import login_required

bp = Blueprint("routes", __name__, url_prefix="/routes")

DIFFICULTY = {"easy": "Лёгкий", "medium": "Средний", "hard": "Сложный"}
SEASONS = {"any": "Любой", "summer": "Лето", "winter": "Зима", "spring_autumn": "Весна/осень"}
TERRAINS = {"any": "Любая", "forest": "Лес", "mountain": "Горы", "city": "Город", "water": "Вода/берег"}
PER_PAGE = 10
PHOTO_TOKEN = re.compile(r"\[фото:(\d{1,9})\]")  # метка фото в тексте: [фото:12]
MAX_PLACES = 50
KINDS = {"curated": "Проверенные", "community": "От путешественников"}
STALE_DAYS = 30  # через сколько дней данные считаются устаревшими

ALLOWED_EXTENSIONS = {
    "jpg": "jpg",
    "jpeg": "jpg",
    "png": "png",
    "webp": "webp",
}


def path_length_km(points):
    """Длина ломаной линии по точкам (формула гаверсинусов)."""
    total = 0.0
    for (lat1, lon1), (lat2, lon2) in zip(points, points[1:]):
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dlon = math.radians(lon2 - lon1)
        a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
        total += 6371 * 2 * math.asin(math.sqrt(a))
    return round(total, 2)


def parse_points(raw):
    try:
        points = [(float(lat), float(lon)) for lat, lon in json.loads(raw)]
    except (ValueError, TypeError):
        return None
    if any(not (-90 <= lat <= 90 and -180 <= lon <= 180) for lat, lon in points):
        return None
    return points


def valid_date(s):
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def num(name):
    try:
        return float(request.args.get(name, "").replace(",", "."))
    except ValueError:
        return None


def _routes_img_dir():
    folder = current_app.config.get("ROUTE_UPLOAD_FOLDER") or os.path.join(
        current_app.static_folder, "img", "routes"
    )
    os.makedirs(folder, exist_ok=True)
    return folder


def _remove_route_images(route_id):
    folder = _routes_img_dir()
    for fname in os.listdir(folder):
        stem, _ = os.path.splitext(fname)
        if stem == str(route_id):
            try:
                os.remove(os.path.join(folder, fname))
            except OSError:
                pass


def _detect_image_ext(file_storage):
    """Проверяет расширение и сигнатуру содержимого файла (JPEG, PNG, WEBP)."""
    if not file_storage or not file_storage.filename:
        return None, None

    _, raw_ext = os.path.splitext(file_storage.filename)
    ext = raw_ext.lstrip(".").lower()
    if not ext:
        return None, "Не удалось определить формат файла."
    if ext not in ALLOWED_EXTENSIONS:
        return None, "Разрешены только изображения JPG, JPEG, PNG или WEBP."

    stream = file_storage.stream
    pos = stream.tell()
    header = stream.read(16)
    stream.seek(pos)

    is_jpeg = header.startswith(b"\xff\xd8\xff")
    is_png = header.startswith(b"\x89PNG\r\n\x1a\n")
    is_webp = len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"

    if not (is_jpeg or is_png or is_webp):
        return None, "Файл повреждён или не является корректным изображением."

    return ALLOWED_EXTENSIONS[ext], None

def save_route_photo(route_id, file_storage, remove_existing=False):
    if remove_existing:
        _remove_route_images(route_id)
    if file_storage and file_storage.filename:
        ext, error = _detect_image_ext(file_storage)
        if error:
            return error
        _remove_route_images(route_id)
        target = os.path.join(_routes_img_dir(), f"{route_id}.{ext}")
        file_storage.save(target)
    return None


INSERT_SQL = """INSERT INTO routes
    (author_id, title, region, length_km, difficulty, days, season, terrain, description,
     restrictions, source_url, source_checked, open_from, open_to, is_public,
     surface, max_slope, has_steps, rest_points)
    VALUES (:author_id, :title, :region, :length_km, :difficulty, :days, :season, :terrain,
     :description, :restrictions, :source_url, :source_checked, :open_from, :open_to,
     :is_public, :surface, :max_slope, :has_steps, :rest_points)"""

UPDATE_SQL = """UPDATE routes SET title=:title, region=:region, length_km=:length_km,
    difficulty=:difficulty, days=:days, season=:season, terrain=:terrain,
    description=:description, restrictions=:restrictions, source_url=:source_url,
    source_checked=:source_checked, open_from=:open_from, open_to=:open_to,
    is_public=:is_public, surface=:surface, max_slope=:max_slope, has_steps=:has_steps,
    rest_points=:rest_points WHERE id=:id AND author_id=:author_id"""


def read_route_form(f):
    def opt(name):
        return f.get(name, "").strip() or None

    title = f.get("title", "").strip()
    region = f.get("region", "").strip()
    description = f.get("description", "").strip()
    source_url = opt("source_url")
    open_from, open_to, source_checked = opt("open_from"), opt("open_to"), opt("source_checked")
    points = parse_points(f.get("points", "[]"))
    places = parse_places(f.get("places"))
    long_fields = [opt("restrictions"), opt("surface"), opt("max_slope"),
                   opt("rest_points"), source_url]
    try:
        days = int(f.get("days", "1"))
    except ValueError:
        days = 0

    error = None
    if not title or not region or not description:
        error = "Заполните название, регион и описание."
    elif len(title) > 120 or len(region) > 100:
        error = "Название не длиннее 120 символов, регион не длиннее 100."
    elif len(description) > 10000 or any(t and len(t) > 1000 for t in long_fields):
        error = "Один из текстов слишком длинный."
    elif (f.get("difficulty") not in DIFFICULTY or f.get("season") not in SEASONS
          or f.get("terrain") not in TERRAINS):
        error = "Выберите значения из списков."
    elif not 1 <= days <= 30:
        error = "Число дней должно быть от 1 до 30."
    elif source_url and not source_url.startswith(("http://", "https://")):
        error = "Ссылка должна начинаться с http:// или https://."
    elif any(d and not valid_date(d) for d in (open_from, open_to, source_checked)):
        error = "Даты введены неверно."
    elif open_from and open_to and open_from > open_to:
        error = "Дата открытия позже даты закрытия."
    elif points is None or len(points) < 2:
        error = "Добавьте на карте минимум две точки маршрута."
    elif places is None:
        error = "Проверьте места на карте: у каждого должно быть название до 80 символов."

    data = {
        "title": title, "region": region,
        "length_km": path_length_km(points) if points else 0,
        "difficulty": f.get("difficulty"), "days": days, "season": f.get("season"),
        "terrain": f.get("terrain"), "description": description,
        "restrictions": opt("restrictions"), "source_url": source_url,
        "source_checked": source_checked, "open_from": open_from, "open_to": open_to,
        "is_public": 1 if f.get("is_public") else 0, "surface": opt("surface"),
        "max_slope": opt("max_slope"), "has_steps": 1 if f.get("has_steps") else 0,
        "rest_points": opt("rest_points"),
    }
    return data, points, places, error


def save_points(db, route_id, points, places):
    db.executemany(
        "INSERT INTO route_points (route_id, position, kind, lat, lon) VALUES (?, ?, 'path', ?, ?)",
        [(route_id, i, lat, lon) for i, (lat, lon) in enumerate(points)],
    )
    db.executemany(
        "INSERT INTO route_points (route_id, position, kind, lat, lon, name, note) "
        "VALUES (?, ?, 'place', ?, ?, ?, ?)",
        [(route_id, i, lat, lon, name, note) for i, (lat, lon, name, note) in enumerate(places)],
    )


def parse_places(raw):
    """Места из формы: JSON-список {lat, lon, name, note}. При ошибке вернёт None."""
    try:
        items = json.loads(raw or "[]")
        if not isinstance(items, list) or len(items) > MAX_PLACES:
            return None
        places = []
        for it in items:
            lat, lon = float(it["lat"]), float(it["lon"])
            name, note = str(it.get("name", "")).strip(), str(it.get("note", "")).strip()
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return None
            if not name or len(name) > 80 or len(note) > 300:
                return None
            places.append((lat, lon, name, note or None))
        return places
    except (ValueError, TypeError, KeyError, AttributeError):
        return None


def load_map_data(db, route_id):
    """Линия маршрута и названные места из базы."""
    rows = db.execute(
        "SELECT kind, lat, lon, name, note FROM route_points WHERE route_id = ? ORDER BY position",
        (route_id,),
    ).fetchall()
    points = [[r["lat"], r["lon"]] for r in rows if r["kind"] == "path"]
    places = [{"lat": r["lat"], "lon": r["lon"], "name": r["name"] or "", "note": r["note"] or ""}
              for r in rows if r["kind"] == "place"]
    return points, places


def form_photos(db, route_id=None):
    """Фото, которые можно вставить в текст: этого маршрута и свежие несохранённые."""
    return db.execute(
        "SELECT id, filename, caption FROM route_photos WHERE user_id = ? AND "
        "(route_id = ? OR (route_id IS NULL AND created_at >= datetime('now', '-1 day'))) ORDER BY id",
        (g.user["id"], route_id or -1),
    ).fetchall()


def sync_photos(db, route_id, description):
    """Привязывает фото из текста к маршруту, а ненужные удаляет из базы.
    Возвращает имена файлов, которые нужно стереть после commit."""
    ids = {int(i) for i in PHOTO_TOKEN.findall(description)}
    for pid in ids:
        db.execute("UPDATE route_photos SET route_id = ? WHERE id = ? AND user_id = ? "
                   "AND (route_id IS NULL OR route_id = ?)", (route_id, pid, g.user["id"], route_id))
    old = db.execute(
        "SELECT id, filename FROM route_photos WHERE route_id = ? OR "
        "(user_id = ? AND route_id IS NULL AND created_at < datetime('now', '-1 day'))",
        (route_id, g.user["id"]),
    ).fetchall()
    gone = [r for r in old if r["id"] not in ids]
    for r in gone:
        db.execute("DELETE FROM route_photos WHERE id = ?", (r["id"],))
    return [r["filename"] for r in gone]


def _posts_dir():
    folder = os.path.join(current_app.static_folder, "img", "posts")
    os.makedirs(folder, exist_ok=True)
    return folder


def _remove_post_files(names):
    for n in names:
        try:
            os.remove(os.path.join(_posts_dir(), n))
        except OSError:
            pass


@bp.app_template_filter("post")
def render_post(text, photos):
    """Описание как пост: абзацы текста и фото на месте меток [фото:N]."""
    out = []
    for i, chunk in enumerate(PHOTO_TOKEN.split(text or "")):
        if i % 2 == 0:
            for para in re.split(r"\n\s*\n", chunk.strip()):
                if para.strip():
                    lines = Markup("<br>").join(escape(l) for l in para.splitlines())
                    out.append(Markup("<p>%s</p>") % lines)
        else:
            photo = photos.get(int(chunk))
            if photo:
                url = url_for("static", filename="img/posts/" + photo["filename"])
                out.append(Markup('<figure class="post-photo"><img src="%s" alt="%s" loading="lazy">'
                                  '<figcaption aria-hidden="true">%s</figcaption></figure>')
                           % (url, photo["caption"], photo["caption"]))
    return Markup("\n").join(out)

def get_own_route(route_id):
    route = get_db().execute("SELECT * FROM routes WHERE id = ?", (route_id,)).fetchone()
    if route is None:
        abort(404)
    if route["author_id"] != g.user["id"]:
        abort(403)
    return route


@bp.route("/new", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        data, points, places, error = read_route_form(request.form)
        photo = request.files.get("photo")
        if error is None and photo and photo.filename:
            _, photo_error = _detect_image_ext(photo)
            if photo_error:
                error = photo_error

        if error is None:
            db = get_db()
            cur = db.execute(INSERT_SQL, {**data, "author_id": g.user["id"]})
            route_id = cur.lastrowid
            save_points(db, route_id, points, places)
            gone = sync_photos(db, route_id, data["description"])
            photo_err = save_route_photo(route_id, photo)
            if photo_err:
                db.rollback()
                flash(photo_err)
            else:
                db.commit()
                _remove_post_files(gone)
                flash("Маршрут сохранён.")
                return redirect(url_for("routes.detail", route_id=route_id))
        else:
            flash(error)
    form = request.form if request.method == "POST" else {"is_public": 1}
    return render_template("route_form.html", form=form, editing=False, route_id=None,
                           photos=form_photos(get_db()),
                           difficulty=DIFFICULTY, seasons=SEASONS, terrains=TERRAINS)


@bp.route("/<int:route_id>/edit", methods=("GET", "POST"))
@login_required
def edit(route_id):
    route = get_own_route(route_id)
    db = get_db()
    if request.method == "POST":
        data, points, places, error = read_route_form(request.form)
        photo = request.files.get("photo")
        remove_photo = bool(request.form.get("remove_photo"))
        if error is None and photo and photo.filename:
            _, photo_error = _detect_image_ext(photo)
            if photo_error:
                error = photo_error

        if error is None:
            db.execute(UPDATE_SQL, {**data, "id": route_id, "author_id": g.user["id"]})
            db.execute("DELETE FROM route_points WHERE route_id = ?", (route_id,))
            save_points(db, route_id, points, places)
            gone = sync_photos(db, route_id, data["description"])
            photo_err = save_route_photo(route_id, photo, remove_existing=remove_photo)
            if photo_err:
                db.rollback()
                flash(photo_err)
            else:
                db.commit()
                _remove_post_files(gone)
                flash("Изменения сохранены.")
                return redirect(url_for("routes.detail", route_id=route_id))
        else:
            flash(error)
        form = request.form
    else:
        points, places = load_map_data(db, route_id)
        form = {**dict(route), "points": json.dumps(points),
                "places": json.dumps(places, ensure_ascii=False)}
    return render_template("route_form.html", form=form, editing=True, route_id=route_id,
                           photos=form_photos(db, route_id),
                           difficulty=DIFFICULTY, seasons=SEASONS, terrains=TERRAINS)

@bp.route("/<int:route_id>/visibility", methods=("POST",))
@login_required
def toggle_visibility(route_id):
    route = get_own_route(route_id)
    db = get_db()
    db.execute("UPDATE routes SET is_public = ? WHERE id = ? AND author_id = ?",
               (0 if route["is_public"] else 1, route_id, g.user["id"]))
    db.commit()
    flash("Видимость маршрута изменена.")
    return redirect(url_for("routes.detail", route_id=route_id))


@bp.route("/<int:route_id>/delete", methods=("POST",))
@login_required
def delete(route_id):
    get_own_route(route_id)
    db = get_db()
    names = [r["filename"] for r in db.execute(
        "SELECT filename FROM route_photos WHERE route_id = ?", (route_id,))]
    db.execute("DELETE FROM routes WHERE id = ? AND author_id = ?", (route_id, g.user["id"]))
    db.commit()
    _remove_route_images(route_id)
    _remove_post_files(names)
    flash("Маршрут удалён.")
    return redirect(url_for("routes.mine"))


@bp.route("/")
def catalog():
    where = ["(r.is_public = 1 OR r.author_id = ?)"]
    params = [g.user["id"] if g.user else -1]
    a = request.args

    if a.get("region", "").strip():
        where.append("r.region LIKE ?")
        params.append("%" + a["region"].strip() + "%")
    if a.get("difficulty") in DIFFICULTY:
        where.append("r.difficulty = ?")
        params.append(a["difficulty"])
    if a.get("season") in SEASONS and a["season"] != "any":
        where.append("r.season IN (?, 'any')")
        params.append(a["season"])
    if a.get("terrain") in TERRAINS and a["terrain"] != "any":
        where.append("r.terrain IN (?, 'any')")
        params.append(a["terrain"])
    if num("min_km") is not None:
        where.append("r.length_km >= ?")
        params.append(num("min_km"))
    if num("max_km") is not None:
        where.append("r.length_km <= ?")
        params.append(num("max_km"))
    if num("days") is not None:
        where.append("r.days = ?")
        params.append(int(num("days")))
    if a.get("no_steps"):
        where.append("r.has_steps = 0")
    if a.get("kind") in KINDS:
        where.append("r.kind = ?")
        params.append(a["kind"])

    order_map = {
        "new": "r.created_at DESC, r.id DESC",
        "popular": "r.views DESC, r.id DESC",
        "short": "r.length_km ASC, r.id DESC",
        "long": "r.length_km DESC, r.id DESC",
    }
    order_sql = order_map.get(a.get("sort", "new"), order_map["new"])

    try:
        page = max(1, int(a.get("page", "1")))
    except ValueError:
        page = 1

    where_sql = " AND ".join(where)
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM routes r WHERE " + where_sql, params).fetchone()[0]
    pages = max(1, math.ceil(total / PER_PAGE))
    page = min(page, pages)

    routes = db.execute(
        "SELECT r.* FROM routes r WHERE " + where_sql +
        f" ORDER BY {order_sql} LIMIT ? OFFSET ?",
        params + [PER_PAGE, (page - 1) * PER_PAGE],
    ).fetchall()

    filters = {k: v for k, v in a.items() if k != "page" and v}
    return render_template("catalog.html", routes=routes, args=a, total=total, page=page,
                           pages=pages, filters=filters, difficulty=DIFFICULTY, terrains=TERRAINS, kinds=KINDS)


@bp.route("/<int:route_id>")
def detail(route_id):
    db = get_db()
    route = db.execute(
        "SELECT r.*, u.username FROM routes r JOIN users u ON u.id = r.author_id WHERE r.id = ?",
        (route_id,),
    ).fetchone()
    if route is None or (not route["is_public"] and (g.user is None or g.user["id"] != route["author_id"])):
        abort(404)

    if g.user is None or g.user["id"] != route["author_id"]:
        db.execute("UPDATE routes SET views = views + 1 WHERE id = ?", (route_id,))
        db.commit()

    points, places = load_map_data(db, route_id)
    photos = {r["id"]: r for r in db.execute(
        "SELECT id, filename, caption FROM route_photos WHERE route_id = ?", (route_id,))}
    gear = db.execute(
        """SELECT name, category FROM gear_items
           WHERE season IN ('any', ?) AND terrain IN ('any', ?) AND min_days <= ?
           ORDER BY category, name""",
        (route["season"], route["terrain"], route["days"]),
    ).fetchall()
    return render_template("route_detail.html", route=route, points=points, gear=gear,
                           difficulty=DIFFICULTY, places=places, photos=photos,)


@bp.route("/mine")
@login_required
def mine():
    routes = get_db().execute(
        "SELECT * FROM routes WHERE author_id = ? ORDER BY created_at DESC, id DESC",
        (g.user["id"],),
    ).fetchall()
    return render_template("my_routes.html", routes=routes, difficulty=DIFFICULTY)

@bp.app_template_global("route_badges")
def route_badges(r):
    """Метки под названием маршрута: список пар (css-класс, текст)."""
    badges = [("verified", "Проверенный маршрут")] if r["kind"] == "curated" \
        else [("community", "От путешественника")]
    if r["is_closed"]:
        badges.append(("closed", "Сейчас закрыт"))
    today = date.today().isoformat()
    if (r["open_from"] and today < r["open_from"]) or (r["open_to"] and today > r["open_to"]):
        badges.append(("warn", "Вне сезона"))
    checked = r["source_checked"]
    if not checked:
        badges.append(("warn", "Дата проверки не указана"))
    else:
        try:
            if (date.today() - date.fromisoformat(checked)).days > STALE_DAYS:
                badges.append(("warn", "Данные могли устареть"))
        except ValueError:
            pass
    return badges

@bp.route("/photo", methods=("POST",))
@limiter.limit("60 per hour")
@login_required
def upload_photo():
    file = request.files.get("photo")
    caption = request.form.get("caption", "").strip()
    if not file or not file.filename:
        return jsonify(error="Выберите файл."), 400
    if not caption or len(caption) > 200:
        return jsonify(error="Опишите фото (до 200 символов)."), 400
    ext, error = _detect_image_ext(file)
    if error:
        return jsonify(error=error), 400
    db = get_db()
    pending = db.execute("SELECT COUNT(*) FROM route_photos WHERE user_id = ? AND route_id IS NULL",
                         (g.user["id"],)).fetchone()[0]
    if pending >= 30:
        return jsonify(error="Слишком много несохранённых фото. Сохраните маршрут."), 400
    name = f"{secrets.token_hex(12)}.{ext}"
    file.save(os.path.join(_posts_dir(), name))
    cur = db.execute("INSERT INTO route_photos (user_id, filename, caption) VALUES (?, ?, ?)",
                     (g.user["id"], name, caption))
    db.commit()
    return jsonify(id=cur.lastrowid, caption=caption,
                   url=url_for("static", filename=f"img/posts/{name}"))