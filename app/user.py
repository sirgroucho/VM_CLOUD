from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Device

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route("/")
@login_required
def dashboard():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template("user/dashboard.html", devices=devices)

@user_bp.route("/devices", methods=["GET","POST"])
@login_required
def devices():
    if request.method == "POST":
        name = request.form["name"]
        device = Device(user_id=current_user.id, name=name, token="dummy-jwt")
        db.session.add(device)
        db.session.commit()
        flash("Device added!", "success")
        return redirect(url_for("user.devices"))
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template("user/devices.html", devices=devices)
