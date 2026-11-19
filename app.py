import os
from flask import Flask, url_for
import db


def ru_days(n):
    """1 день, 2 дня, 5 дней."""
    n = int(n)
    if 11 <= n % 100 <= 14:
        word = "дней"
    elif n % 10 == 1:
        word = "день"
    elif 2 <= n % 10 <= 4:
        word = "дня"
    else:
        word = "дней"
    return f"{n} {word}"


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")
    db.init_app(app)

    from views import auth, pages, routes
    app.register_blueprint(auth.bp)
    app.register_blueprint(pages.bp)
    app.register_blueprint(routes.bp)

    def route_image(route_id):
        """Фото маршрута, если оно лежит в static/img/routes, иначе заглушка."""
        for ext in ("jpg", "jpeg", "png", "webp"):
            rel = f"img/routes/{route_id}.{ext}"
            if os.path.exists(os.path.join(app.static_folder, rel)):
                return url_for("static", filename=rel)
        return url_for("static", filename="img/route-placeholder.png")

    app.jinja_env.filters["ru_days"] = ru_days
    app.jinja_env.globals.update(
        route_image=route_image,
        SEASONS=routes.SEASONS,
        DIFFICULTY=routes.DIFFICULTY,
        TERRAINS=routes.TERRAINS,
    )
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
