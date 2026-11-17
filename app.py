from flask import Flask

import db


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")

    db.init_app(app)

    from views import auth, pages, routes
    app.register_blueprint(auth.bp)
    app.register_blueprint(pages.bp)
    app.register_blueprint(routes.bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)