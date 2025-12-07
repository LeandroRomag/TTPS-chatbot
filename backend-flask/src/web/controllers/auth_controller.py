from flask import Blueprint, render_template, redirect, url_for
from src.core.auth.user import User
from src.core.database import db

authentication_blueprint = Blueprint("authentication", __name__, url_prefix="/auth")

@authentication_blueprint.get("/login")
def login():
    return render_template("login.html")

@authentication_blueprint.post("/login")
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")

    user = db.session.query(User).filter_by(email=email).first()

    if not user or not user.check_password(password):
        return render_template("login.html", error="Credenciales incorrectas")

    session["user_id"] = user.id
    return redirect(url_for("authentication.dashboard"))

@authentication_blueprint.get("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page='inicio')

@authentication_blueprint.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("authentication.login"))
