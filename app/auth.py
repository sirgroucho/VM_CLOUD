from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db, login_manager, limiter
from .audit import audit

auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config.get("RATE_LIMIT_LOGIN", "5 per minute"), methods=["POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user: User | None = User.query.filter_by(email=email).first()
        if not user or not user.is_active or not user.check_password(password):
            audit("login_failed", target_type="user", meta={"email": email})
            flash("Invalid credentials", "error")
            return render_template("login.html")
        login_user(user)
        audit("login_success", actor_user_id=user.id)
        return redirect(url_for("user.dashboard"))
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    audit("logout", actor_user_id=current_user.id)
    logout_user()
    return redirect(url_for("auth.login"))
