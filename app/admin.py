from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from models import Application, Blacklist

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "admin":
            flash("Admins only", "error")
            return redirect(url_for("user.dashboard"))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    apps = Application.query.all()
    return render_template("admin/dashboard.html", apps=apps)

@admin_bp.route("/applications")
@login_required
@admin_required
def applications():
    apps = Application.query.all()
    return render_template("admin/applications.html", apps=apps)

@admin_bp.route("/blacklist", methods=["GET","POST"])
@login_required
@admin_required
def blacklist():
    if request.method == "POST":
        ip = request.form["ip"]
        reason = request.form.get("reason","")
        entry = Blacklist(ip=ip, reason=reason)
        db.session.add(entry)
        db.session.commit()
        flash("IP blacklisted", "success")
    entries = Blacklist.query.all()
    return render_template("admin/blacklist.html", entries=entries)
