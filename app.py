"""
EcoBuild — Flask application factory.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template


# ── Load .env for local development ───────────────────────────────────────────
# On Render, environment variables are provided by Render itself.
load_dotenv(Path(__file__).resolve().parent / ".env")


def create_app():
    app = Flask(__name__)

    # ── Configuration ─────────────────────────────────────────────────────────
    from config import get_config

    app.config.from_object(get_config())

    # ── Extensions ────────────────────────────────────────────────────────────
    from extensions import csrf, db, login_manager, migrate

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "warning"

    # ── User loader ────────────────────────────────────────────────────────────
    from database.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.public import public_bp
    from routes.user import user_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # ── Error handlers ─────────────────────────────────────────────────────────
    @app.errorhandler(401)
    def unauthorized(e):
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


# ── Application Instance for Gunicorn / Render ────────────────────────────────
# Render Start Command:
# gunicorn app:app
app = create_app()


# ── Local Development ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=app.config.get("DEBUG", False)
    )