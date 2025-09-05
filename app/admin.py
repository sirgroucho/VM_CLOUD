from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Application, User, Service, UserService, Device, AuditLog
from . import db
from .audit import audit
import secrets

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Admins only", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    pending = Application.query.filter_by(status="pending").all()
    users = User.query.order_by(User.created_at.desc()).limit(20).all()
    return render_template("admin/dashboard.html", pending=pending, users=users)

@admin_bp.route("/applications/<int:app_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve(app_id: int):
    a = db.session.get(Application, app_id)
    if not a:
        flash("Application not found", "error")
        return redirect(url_for("admin.dashboard"))
    # Create user if missing
    user = User.query.filter_by(email=a.email.lower()).first()
    created = False
    temp_password = None
    if not user:
        user = User(email=a.email.lower(), role="user", is_active=True)
        temp_password = secrets.token_urlsafe(12)
        user.set_password(temp_password)
        db.session.add(user)
        created = True
    # Determine service approvals
    requested = [c for c in (a.requested_services or "").split(",") if c]
    selected = request.form.getlist("services") or requested
    services = Service.query.filter(Service.code.in_(selected)).all()
    # Add missing links
    for svc in services:
        if not any(us.service_id == svc.id for us in user.services):
            db.session.add(UserService(user_id=user.id, service_id=svc.id, role="member"))
    a.status = "accepted"
    db.session.commit()
    audit("application_approved", actor_user_id=current_user.id, target_type="application", target_id=a.id, meta={"user_id": user.id, "services": selected, "created": created})
    flash("Approved. User created." if created else "Approved.", "success")
    if created and temp_password:
        flash(f"Temp password for {user.email}: {temp_password}", "info")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/applications/<int:app_id>/deny", methods=["POST"])
@login_required
@admin_required
def deny(app_id: int):
    a = db.session.get(Application, app_id)
    if not a:
        flash("Application not found", "error")
        return redirect(url_for("admin.dashboard"))
    a.status = "denied"
    a.reason = request.form.get("reason","")
    db.session.commit()
    audit("application_denied", actor_user_id=current_user.id, target_type="application", target_id=a.id, meta={"reason": a.reason})
    flash("Denied.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/users/<int:user_id>/services", methods=["GET","POST"])
@login_required
@admin_required
def edit_user_services(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("admin.dashboard"))
    all_services = Service.query.filter_by(is_active=True).all()
    if request.method == "POST":
        selected = set(request.form.getlist("services"))
        # remove unselected
        for us in list(user.services):
            if us.service.code not in selected:
                db.session.delete(us)
        # add selected
        for svc in all_services:
            if svc.code in selected and not any(x.service_id == svc.id for x in user.services):
                db.session.add(UserService(user_id=user.id, service_id=svc.id, role="member"))
        db.session.commit()
        audit("user_services_updated", actor_user_id=current_user.id, target_type="user", target_id=user.id, meta={"services": list(selected)})
        flash("Services updated", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/user_services.html", user=user, all_services=all_services)

@admin_bp.route("/audit")
@login_required
@admin_required
def audit_view():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return render_template("admin/applications.html", logs=logs)
