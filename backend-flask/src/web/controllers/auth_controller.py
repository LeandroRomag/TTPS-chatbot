from flask import Blueprint, render_template, redirect, url_for

authentication_blueprint = Blueprint("authentication", __name__, url_prefix="/auth")

@authentication_blueprint.get("/login")
def login():
    return render_template("login.html")

@authentication_blueprint.post("/login")
def login_post():
    # TODO: Implement login logic with session management
    # On success: redirect to dashboard
    # On failure: return to login with error message
    return redirect(url_for("authentication.dashboard"))

@authentication_blueprint.get("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page='inicio')

@authentication_blueprint.get("/logout")
def logout():
    # TODO: Implement logout logic (clear session)
    return redirect(url_for("authentication.login"))
