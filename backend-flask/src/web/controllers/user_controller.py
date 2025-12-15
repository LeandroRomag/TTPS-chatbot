from flask import Blueprint, render_template, redirect, url_for, request, flash
from src.core.auth.user import User, UserRole
from src.core.database import db

user_blueprint = Blueprint("user", __name__, url_prefix="/user")
@user_blueprint.get("/")
def index():
    admins = (
        db.session.query(User)
        .filter(User.role == UserRole.ADMIN)
        .order_by(User.created_at.desc())
        .all()
    )

    return render_template(
        "user/index.html",
        admins=admins,
        active_page="usuarios"
    )


@user_blueprint.post("/<int:user_id>/delete")
def delete(user_id):
    user = db.session.get(User, user_id)

    if not user or user.role != UserRole.ADMIN:
        flash("Administrador no encontrado", "danger")
        return redirect(url_for("user.index"))

    db.session.delete(user)
    db.session.commit()

    flash("Administrador eliminado", "success")
    return redirect(url_for("user.index"))


@user_blueprint.get("/create")
def create():
    return render_template("user/create.html", active_page='usuarios')

@user_blueprint.post("/create")
def create_post():
    nombre = request.form.get("nombre")
    apellido = request.form.get("apellido")
    email = request.form.get("email")
    password = request.form.get("password")

    # Validaciones básicas
    if not all([nombre, apellido, email, password]):
        flash("Todos los campos son obligatorios", "danger")
        return render_template("user/create.html", active_page="usuarios")

    # Verificar email duplicado
    existing_user = db.session.query(User).filter_by(email=email).first()
    if existing_user:
        flash("El email ya está registrado", "danger")
        return render_template("user/create.html", active_page="usuarios")

    # Hash de contraseña
    password_hash = generate_password_hash(password)

    # Crear administrador
    user = User(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password_hash=password_hash,
        system_admin=True,
        role=UserRole.ADMIN,
        active=True
    )

    db.session.add(user)
    db.session.commit()

    flash("Administrador creado correctamente", "success")
    return redirect(url_for("user.index"))