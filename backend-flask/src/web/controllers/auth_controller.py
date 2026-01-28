from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from functools import wraps
from src.core.auth.user import User
from src.core.database import db
from src.core.services import user_services

authentication_blueprint = Blueprint("authentication", __name__, url_prefix="/auth")


# ============================================================
# Login Control
# ============================================================

def login_required(f):
    """
    Decorador para proteger vistas que requieren autenticación.
    Redirige a login si el usuario no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión para acceder a esta página.", "warning")
            return redirect(url_for("authentication.login"))
        
        user = user_services.get_user_by_id(session["user_id"])
        if not user or not user.is_active:
            session.clear()
            flash("Usuario inactivo o eliminado.", "error")
            return redirect(url_for("authentication.login"))
        
        return f(*args, **kwargs)
    return decorated_function


@authentication_blueprint.get("/login")
def login():
    """
    Muestra la página de login.
    Si el usuario ya está autenticado, lo redirige al dashboard.
    """
    if "user_id" in session:
        user = user_services.get_user_by_id(session["user_id"])
        if user and user.is_active:
            return redirect(url_for("authentication.dashboard"))
    
    return render_template("login.html")


@authentication_blueprint.post("/login")
def login_post():
    """
    Procesa el login del usuario.
    Valida email y contraseña contra la base de datos.
    """
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # Validación básica
    if not email or not password:
        return render_template("login.html", error="Email y contraseña son requeridos.")

    # Buscar usuario en la base de datos
    user = user_services.get_user_by_email(email, include_deleted=False)

    # Validar credenciales y estado del usuario
    if not user:
        return render_template("login.html", error="Email o contraseña incorrectos.")
    
    if not user.is_active:
        return render_template("login.html", error="Usuario inactivo. Contacta al administrador.")
    
    if not user.check_password(password):
        return render_template("login.html", error="Email o contraseña incorrectos.")

    # Login exitoso: crear sesión
    session.clear()
    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.full_name
    
    flash(f"Bienvenido, {user.full_name}!", "success")
    return redirect(url_for("authentication.dashboard"))


@authentication_blueprint.get("/dashboard")
@login_required
def dashboard():
    """
    Muestra el dashboard del usuario.
    Requiere estar autenticado.
    """
    user = user_services.get_user_by_id(session["user_id"])
    return render_template("dashboard.html", active_page='inicio', user=user)


@authentication_blueprint.get("/logout")
def logout():
    """
    Cierra la sesión del usuario.
    """
    user_name = session.get("user_name", "Usuario")
    session.clear()
    flash(f"Hasta luego, {user_name}!", "info")
    return redirect(url_for("authentication.login"))
