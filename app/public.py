from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Application
import ipaddress

public_bp = Blueprint("public", __name__)

@public_bp.route("/apply", methods=["GET","POST"])
def apply():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        services = ",".join(request.form.getlist("services"))
        ip = request.remote_addr
        app = Application(name=name, email=email, services=services, ip=ip)
        db.session.add(app)
        db.session.commit()
        flash("Application submitted!", "success")
        return redirect(url_for("public.apply"))
    return render_template("apply.html")
