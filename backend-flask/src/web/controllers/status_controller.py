from flask import Blueprint, render_template
from src.web.controllers.auth_controller import login_required
# Importamos la función lógica que acabamos de crear en el Paso 1
from src.core.status_service import get_system_status
import datetime

status_blueprint = Blueprint("status", __name__, url_prefix="/status")

@status_blueprint.get("/")
@login_required
def index():
    # Llamamos al servicio para obtener los datos frescos
    services = get_system_status()
    
    # Obtenemos la hora actual para mostrar en el panel
    last_check = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return render_template(
        "system/status.html",
        services=services,
        last_check=last_check,
        active_page="estado" # Esto activa el ítem en el menú lateral
    )