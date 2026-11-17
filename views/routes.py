import json
import math
from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from db import get_db
from views.auth import login_required

bp = Blueprint("routes", __name__, url_prefix="/routes")

DIFFICULTY = {"easy": "Лёгкий", "medium": "Средний", "hard": "Сложный"}
SEASONS = {"any": "Любой", "summer": "Лето", "winter": "Зима", "spring_autumn": "Весна/осень"}
TERRAINS = {"any": "Любая", "forest": "Лес", "mountain": "Горы", "city": "Город", "water": "Вода/берег"}
PER_PAGE = 10

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
    """Превращает текст '[[lat, lon], ...]' в список; при ошибке возвращает None."""
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
    """Число из адресной строки или None, если там не число."""
    try:
        return float(request.args.get(name, "").replace(",", "."))
    except ValueError:
        return None


@bp.route("/new", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        f = request.form

        def opt(name):
            return f.get(name, "").strip() or None

        title = f.get("title", "").strip()
        region = f.get("region", "").strip()
        description = f.get("description", "").strip()
        source_url = opt("source_url")
        points = parse_points(f.get("points", "[]"))
        open_from, open_to = opt("open_from"), opt("open_to")
        source_checked = opt("source_checked")
        is_public = 1 if f.get("is_public") else 0
        try:
            days = int(f.get("days", "1"))
        except ValueError:
            days = 0

        error = None
        if not title or not region or not description:
            error = "Заполните название, регион и описание."
        elif len(title) > 120:
            error = "Название не длиннее 120 символов."
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

        if error is None:
            db = get_db()
            cur = db.execute(
                """INSERT INTO routes
                   (author_id, title, region, length_km, difficulty, days, season, terrain,
                    description, restrictions, source_url, source_checked, open_from, open_to,
                    is_public, surface, max_slope, has_steps, rest_points)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (g.user["id"], title, region, path_length_km(points), f["difficulty"], days,
                 f["season"], f["terrain"], description, opt("restrictions"), source_url,
                 source_checked, open_from, open_to, is_public, opt("surface"),
                 opt("max_slope"), 1 if f.get("has_steps") else 0, opt("rest_points")),
            )
            db.executemany(
                "INSERT INTO route_points (route_id, position, lat, lon) VALUES (?, ?, ?, ?)",
                [(cur.lastrowid, i, lat, lon) for i, (lat, lon) in enumerate(points)],
            )
            db.commit()
            flash("Маршрут сохранён.")
            return redirect(url_for("routes.detail", route_id=cur.lastrowid))

    return render_template("route_form.html", form=request.form,
                           difficulty=DIFFICULTY, seasons=SEASONS, terrains=TERRAINS)
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
        " ORDER BY r.created_at DESC, r.id DESC LIMIT ? OFFSET ?",
        params + [PER_PAGE, (page - 1) * PER_PAGE],
    ).fetchall()

    filters = {k: v for k, v in a.items() if k != "page" and v}
    return render_template("catalog.html", routes=routes, args=a, total=total, page=page,
                           pages=pages, filters=filters, difficulty=DIFFICULTY, terrains=TERRAINS)


@bp.route("/<int:route_id>")
def detail(route_id):
    db = get_db()
    route = db.execute(
        "SELECT r.*, u.username FROM routes r JOIN users u ON u.id = r.author_id WHERE r.id = ?",
        (route_id,),
    ).fetchone()
    if route is None or (not route["is_public"] and (g.user is None or g.user["id"] != route["author_id"])):
        abort(404)

    points = [[p["lat"], p["lon"]] for p in db.execute(
        "SELECT lat, lon FROM route_points WHERE route_id = ? ORDER BY position", (route_id,))]
    gear = db.execute(
        """SELECT name, category FROM gear_items
           WHERE season IN ('any', ?) AND terrain IN ('any', ?) AND min_days <= ?
           ORDER BY category, name""",
        (route["season"], route["terrain"], route["days"]),
    ).fetchall()
    return render_template("route_detail.html", route=route, points=points, gear=gear,
                           difficulty=DIFFICULTY)


@bp.route("/mine")
@login_required
def mine():
    routes = get_db().execute(
        "SELECT * FROM routes WHERE author_id = ? ORDER BY created_at DESC, id DESC",
        (g.user["id"],),
    ).fetchall()
    return render_template("my_routes.html", routes=routes, difficulty=DIFFICULTY)
