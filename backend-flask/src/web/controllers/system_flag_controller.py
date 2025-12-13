from flask import Blueprint, render_template, redirect, url_for, flash, request
from src.core.services import system_flag_services
from src.core.auth.system_flag import SystemFlagType

system_flag_blueprint = Blueprint("system_flag", __name__, url_prefix="/system_flag")


@system_flag_blueprint.get("/")
def index():
    """Muestra todas las flags del sistema y los tipos disponibles para crear."""
    flags = system_flag_services.get_all_flags()
    available_types = system_flag_services.get_available_flag_types()
    return render_template("system_flag/index.html", flags=flags, available_types=available_types)


@system_flag_blueprint.post("/create")
def create():
    """Crea una nueva flag del sistema."""
    flag_type_value = request.form.get("flag_type")
    
    if not flag_type_value:
        flash("Debe especificar el tipo de flag", "error")
        return redirect(url_for("system_flag.index"))
    
    # Validar que sea un tipo válido
    try:
        flag_type = SystemFlagType(flag_type_value)
    except ValueError:
        flash(f"Tipo de flag inválido: {flag_type_value}", "error")
        return redirect(url_for("system_flag.index"))
    
    # Verificar si ya existe
    if system_flag_services.get_flag_by_type(flag_type):
        flash(f"La flag '{flag_type.name}' ya existe", "warning")
        return redirect(url_for("system_flag.index"))
    
    system_flag_services.create_flag(flag_type)
    flash(f"Flag '{flag_type.name}' creada correctamente", "success")
    return redirect(url_for("system_flag.index"))


@system_flag_blueprint.post("/<int:flag_id>/toggle")
def toggle(flag_id: int):
    """Alterna el estado de una flag del sistema."""
    result = system_flag_services.toggle_flag(flag_id)
    if result is True:
        flash("Estado de la flag actualizado", "success")
    else:
        flash("No se encontró la flag", "error")
    return redirect(url_for("system_flag.index"))


@system_flag_blueprint.post("/<int:flag_id>/delete")
def delete(flag_id: int):
    """Elimina una flag del sistema."""
    result = system_flag_services.delete_flag(flag_id)
    if result is True:
        flash("Flag eliminada correctamente", "success")
    else:
        flash("No se encontró la flag", "error")
    return redirect(url_for("system_flag.index"))
