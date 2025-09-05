from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

def create_app():
    # Load env from mounted secrets (fallback path works in docker or local)
    load_dotenv(dotenv_path=os.environ.get("ENV_PATH", "/app/../secrets/.env"), override=True)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["JWT_SECRET"] = os.environ.get("JWT_SECRET", "dev-jwt-change-me")

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Inline Postgres service defaults (Docker network: db)
        pg_user = os.environ.get("POSTGRES_USER", "appuser")
        pg_pass = os.environ.get("POSTGRES_PASSWORD", "apppass")
        pg_db = os.environ.get("POSTGRES_DB", "appdb")
        db_url = f"postgresql+psycopg2://{pg_user}:{pg_pass}@db:5432/{pg_db}"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Rate limits
    app.config["RATE_LIMIT_LOGIN"] = os.environ.get("RATE_LIMIT_LOGIN", "5 per minute")
    app.config["RATE_LIMIT_APPLY"] = os.environ.get("RATE_LIMIT_APPLY", "10 per minute")

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "auth.login"

    # Provide csrf_token() in templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    # Blueprints
    from .auth import auth_bp
    from .public import public_bp
    from .user import user_bp
    from .admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Seed initial data & admin on first run
    from .seed import seed_initial
    with app.app_context():
        db.create_all()
        seed_initial(app)

    @app.before_request
    def attach_request_meta():
        g.client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        g.user_agent = request.headers.get("User-Agent", "unknown")

    return app
