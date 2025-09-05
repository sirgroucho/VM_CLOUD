from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Device, UserService
from . import db
from .security import mint_device_token, revoke_device
from .audit import audit

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route("/")
@login_required
def dashboard():
    svc_links = [us.service for us in UserService.query.filter_by(user_id=current_user.id).all()]
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template("user/dashboard.html", services=svc_links, devices=devices)

@user_bp.route("/devices", methods=["POST"])
@login_required
def add_device():
    name = request.form.get("name","").strip() or "My device"
    long_lived = request.form.get("long_lived") == "on"
    if long_lived and current_user.role != "admin":
        long_lived = False
    services = [us.service.code for us in UserService.query.filter_by(user_id=current_user.id).all()]
    token, d = mint_device_token(current_user.id, current_user.role, services, long_lived=long_lived)
    d.name = name
    db.session.commit()
    audit("device_issued", actor_user_id=current_user.id, target_type="device", target_id=d.id, meta={"name": name, "long_lived": long_lived})
    return render_template("user/token_issued.html", token=token, device=d)

@user_bp.route("/devices/revoke/<int:device_id>", methods=["POST"])
@login_required
def revoke(device_id: int):
    d = db.session.get(Device, device_id)
    if not d or d.user_id != current_user.id:
        flash("Not found", "error")
        return redirect(url_for("user.dashboard"))
    revoke_device(d)
    audit("device_revoked", actor_user_id=current_user.id, target_type="device", target_id=d.id)
    flash("Device revoked", "success")
    return redirect(url_for("user.dashboard"))
