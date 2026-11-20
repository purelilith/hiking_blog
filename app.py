import os
from flask import Flask, flash, redirect, request, url_for
from werkzeug.exceptions import RequestEntityTooLarge
import db
from extensions import csrf, limiter, oauth


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
    csrf.init_app(app)
    limiter.init_app(app)
    oauth.init_app(app)
    if app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET"):
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    with app.app_context():
        db.ensure_schema()

    @app.context_processor
    def inject_auth():
        return {"google_enabled": bool(app.config.get("GOOGLE_CLIENT_ID")
                                       and app.config.get("GOOGLE_CLIENT_SECRET"))}

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        if app.config.get("SESSION_COOKIE_SECURE"):
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return resp

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_file(_err):
        flash("Файл слишком большой. Максимальный размер фото — 5 МБ.")
        return redirect(request.referrer or url_for("routes.mine"))

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
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")