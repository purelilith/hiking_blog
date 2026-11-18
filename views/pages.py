from flask import Blueprint, jsonify, render_template, request

from db import get_db

bp = Blueprint("pages", __name__)
PAGE = 5  # сколько маршрутов показывать за раз


def popular(offset):
    """Следующие PAGE публичных маршрутов по просмотрам и признак, что есть ещё."""
    rows = get_db().execute(
        "SELECT * FROM routes WHERE is_public = 1 ORDER BY views DESC, id DESC LIMIT ? OFFSET ?",
        (PAGE + 1, offset),
    ).fetchall()
    return rows[:PAGE], len(rows) > PAGE


@bp.route("/")
def index():
    routes, has_more = popular(0)
    return render_template("index.html", routes=routes, has_more=has_more)


@bp.route("/popular")
def popular_more():
    try:
        offset = max(0, int(request.args.get("offset", "0")))
    except ValueError:
        offset = 0
    routes, has_more = popular(offset)
    html = "".join(render_template("_route_card.html", r=r) for r in routes)
    return jsonify(html=html, has_more=has_more)


@bp.route("/about")
def about():
    return render_template("about.html")