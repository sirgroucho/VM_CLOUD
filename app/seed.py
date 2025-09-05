import os
from .models import Service, User
from . import db

def seed_initial(app):
    # Seed default services
    default = [
        ("minecraft", "Minecraft"),
        ("media", "Media"),
        ("nextcloud", "Nextcloud"),
    ]
    for code, name in default:
        if not Service.query.filter_by(code=code).first():
            db.session.add(Service(code=code, name=name))
    db.session.commit()

    # Bootstrap admin if none exist
    admin_exists = User.query.filter_by(role="admin").first() is not None
    if not admin_exists:
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")
        if email and password:
            u = User(email=email.lower(), role="admin", is_active=True)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            app.logger.info(f"Bootstrapped admin {email}")
        else:
            app.logger.warning("No admin exists and ADMIN_EMAIL/ADMIN_PASSWORD not provided. Create one manually.")
