from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .models import Application, Service
from . import db, limiter
from .audit import audit

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    return redirect(url_for("auth.login"))

@public_bp.route("/apply", methods=["GET","POST"])
@limiter.limit(lambda: current_app.config.get("RATE_LIMIT_APPLY", "10 per minute"), methods=["POST"])
def apply():
    services = Service.query.filter_by(is_active=True).all()
    if request.method == "POST":
        # Honeypot field
        if request.form.get("website"):
            return redirect(url_for("public.apply"))
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        requested = request.form.getlist("services")
        svc_csv = ",".join(requested)
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        ua = request.headers.get("User-Agent","unknown")
        app = Application(name=name, email=email, requested_services=svc_csv, ip=ip, ua=ua)
        db.session.add(app)
        db.session.commit()
        audit("apply_submit", target_type="application", target_id=app.id, meta={"email": email, "services": requested})
        flash("Application submitted! An admin will review.", "success")
        return redirect(url_for("public.apply"))
    return render_template("apply.html", services=services)
