from flask import Blueprint, render_template, request, flash, redirect, url_for
from src.web.controllers.auth_controller import login_required
from src.core.config_service import get_config, set_config

system_blueprint = Blueprint("system", __name__, url_prefix="/system")

@system_blueprint.route("/pause", methods=["GET", "POST"])
@login_required
def pause():
    if request.method == "POST":
        # 1. Obtener datos del form
        # Si el checkbox no viene, es False
        is_paused = "true" if request.form.get("is_paused") else "false" 
        message = request.form.get("message")

        # 2. Guardar en BD
        try:
            set_config("maintenance_mode", is_paused)
            set_config("maintenance_message", message)
            flash("Configuración del sistema actualizada.", "success")
        except Exception as e:
            flash(f"Error al guardar: {e}", "danger")
        
        return redirect(url_for("system.pause"))

    # GET: Mostrar estado actual
    current_status = get_config("maintenance_mode", "false") == "true"
    current_message = get_config("maintenance_message", "El sistema se encuentra temporalmente suspendido por mantenimiento.")

    return render_template(
        "system/pause.html", 
        active_page="pausa", # Para que se ilumine en el sidebar
        is_paused=current_status, 
        message=current_message
    )