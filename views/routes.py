import json
import math

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from db import get_db
from views.auth import login_required

bp = Blueprint("routes", __name__, url_prefix="/routes")

DIFFICULTY = {"easy": "Лёгкий", "medium": "Средний", "hard": "Сложный"}
SEASONS = {"any": "Любой", "summer": "Лето", "winter": "Зима", "spring_autumn": "Весна/осень"}
TERRAINS = {"any": "Любая", "forest": "Лес", "mountain": "Горы", "city": "Город", "water": "Вода/берег"}


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
        elif points is None or len(points) < 2:
            error = "Добавьте на карте минимум две точки маршрута."

        if error is None:
            db = get_db()
            cur = db.execute(
                """INSERT INTO routes
                   (author_id, title, region, length_km, difficulty, days, season, terrain,
                    description, restrictions, source_url, source_checked,
                    surface, max_slope, has_steps, rest_points)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (g.user["id"], title, region, path_length_km(points), f["difficulty"], days,
                 f["season"], f["terrain"], description, opt("restrictions"), source_url,
                 opt("source_checked"), opt("surface"), opt("max_slope"),
                 1 if f.get("has_steps") else 0, opt("rest_points")),
            )
            db.executemany(
                "INSERT INTO route_points (route_id, position, lat, lon) VALUES (?, ?, ?, ?)",
                [(cur.lastrowid, i, lat, lon) for i, (lat, lon) in enumerate(points)],
            )
            db.commit()
            flash("Маршрут сохранён.")
            return redirect(url_for("pages.index"))  # позже заменим на страницу маршрута
        flash(error)

    return render_template("route_form.html", form=request.form,
                           difficulty=DIFFICULTY, seasons=SEASONS, terrains=TERRAINS)