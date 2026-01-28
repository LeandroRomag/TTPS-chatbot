from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from src.core.services import user_services
from src.core.auth import auth
from src.core.auth.user import UserRole
from src.web.controllers.auth_controller import login_required

user_blueprint = Blueprint("user", __name__, url_prefix="/user")


# ============================================================
# Listar Usuarios
# ============================================================

@user_blueprint.get("/")
@login_required
def index():
    """Lista todos los usuarios activos (no eliminados)"""
    users = user_services.get_all_users(include_deleted=False)
    return render_template("user/index.html", active_page='usuarios', users=users)


# ============================================================
# Crear Usuario
# ============================================================

@user_blueprint.get("/create")
@login_required
def create():
    """Muestra el formulario para crear un nuevo usuario"""
    return render_template("user/create.html", active_page='usuarios')


@user_blueprint.post("/create")
@login_required
def create_post():
    """Procesa la creación de un nuevo usuario"""
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Validaciones
    if not all([nombre, apellido, email, password]):
        flash("Todos los campos son requeridos.", "error")
        return render_template("user/create.html", active_page='usuarios')

    # Validar email
    if not auth.is_valid_email(email):
        flash("Email no válido.", "error")
        return render_template("user/create.html", active_page='usuarios')

    # Verificar que las contraseñas coincidan
    if password != confirm_password:
        flash("Las contraseñas no coinciden.", "error")
        return render_template("user/create.html", active_page='usuarios')

    # Validar fortaleza de contraseña
    is_valid, msg = auth.is_valid_password(password)
    if not is_valid:
        flash(f"Contraseña débil: {msg}", "error")
        return render_template("user/create.html", active_page='usuarios')

    # Verificar que el email no exista
    if user_services.email_exists(email):
        flash("Email ya registrado.", "error")
        return render_template("user/create.html", active_page='usuarios')

    # Crear usuario
    try:
        user = user_services.create_user(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=auth.generate_password_for_user(password),
            role=UserRole.ADMIN,
            system_admin=False,
            active=True
        )
        flash(f"Usuario {user.full_name} creado exitosamente.", "success")
        return redirect(url_for("user.index"))
    except Exception as e:
        flash(f"Error al crear usuario: {str(e)}", "error")
        return render_template("user/create.html", active_page='usuarios')


# ============================================================
# Eliminar Usuario (Soft Delete)
# ============================================================

@user_blueprint.delete("/<int:user_id>")
@login_required
def delete(user_id: int):
    """Elimina lógicamente un usuario (soft delete).
    No permite eliminar al superadmin."""
    
    # Obtener el usuario a eliminar
    user = user_services.get_user_by_id(user_id)
    
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado."}), 404
    
    # No permitir eliminar al superadmin
    if user.is_sysadmin:
        return jsonify({"success": False, "message": "No se puede eliminar al administrador del sistema."}), 403
    
    # No permitir auto-eliminarse
    from flask import session
    current_user_id = session.get("user_id")
    if user_id == current_user_id:
        return jsonify({"success": False, "message": "No puedes eliminar tu propia cuenta."}), 403
    
    try:
        # Realizar soft delete
        user_services.delete_user(user_id)
        return jsonify({
            "success": True, 
            "message": f"Usuario {user.full_name} eliminado exitosamente."
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error al eliminar usuario: {str(e)}"}), 500
