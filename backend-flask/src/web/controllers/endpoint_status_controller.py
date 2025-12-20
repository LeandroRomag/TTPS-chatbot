"""
Controller para el monitoreo de endpoints.
Proporciona vistas para ver el estado y ejecutar verificaciones manuales.
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from src.core.services import endpoint_monitor_service
from src.core.scheduler import get_next_run_time, is_scheduler_running

endpoint_status_blueprint = Blueprint(
    'endpoint_status', 
    __name__, 
    url_prefix='/admin/endpoints'
)


@endpoint_status_blueprint.route('/')
def index():
    """Vista principal del estado de todos los endpoints."""
    endpoints = endpoint_monitor_service.get_all_status()
    summary = endpoint_monitor_service.get_status_summary()
    
    return render_template(
        'endpoint_status/index.html',
        endpoints=endpoints,
        summary=summary,
        next_check=get_next_run_time(),
        scheduler_running=is_scheduler_running()
    )


@endpoint_status_blueprint.route('/check/<int:endpoint_id>', methods=['POST'])
def manual_check(endpoint_id):
    """Verificación manual de un endpoint específico."""
    endpoint = endpoint_monitor_service.manual_check(endpoint_id)
    
    if endpoint:
        flash(f'Endpoint "{endpoint.name}" verificado: {endpoint.status.value}', 'success')
    else:
        flash('Endpoint no encontrado', 'danger')
    
    return redirect(url_for('endpoint_status.index'))


@endpoint_status_blueprint.route('/check-all', methods=['POST'])
def check_all():
    """Verificación manual de todos los endpoints."""
    results = endpoint_monitor_service.check_all_endpoints()
    healthy = sum(1 for r in results if r.status.value == 'healthy')
    
    flash(f'Verificación completada: {healthy}/{len(results)} endpoints saludables', 'success')
    return redirect(url_for('endpoint_status.index'))
