import os
import requests
from src.core.board.status import HealthCheckResult, HttpMethod, MonitoredEndpoint, ServiceStatus

# --- Configuración de endpoints monitoreados ---

FACULTY_BASE_URL = os.getenv("FACULTY_API_URL", "https://gestiondocente.info.unlp.edu.ar")
CONTENT_BASE_URL = os.getenv("CONTENT_API_URL", "https://gestionapp.info.unlp.edu.ar/api")
N8N_BASE_URL = os.getenv("N8N_HOST", "http://localhost:5678")

ENDPOINTS = {
    "faculty_api": MonitoredEndpoint(
        id="faculty_api",
        name="Estado Facultad",
        url=f"{FACULTY_BASE_URL}/reservas/api/consulta/estadoactual",
        method=HttpMethod.GET,
        timeout=5,
        description="Estado actual de la facultad y horarios.",
        icon="bi-mortarboard",
    ),
    "materias": MonitoredEndpoint(
        id="materias",
        name="API Materias",
        url=f"{FACULTY_BASE_URL}/api/v2/materias.json",
        method=HttpMethod.GET,
        timeout=5,
        description="Catálogo de materias disponibles.",
        icon="bi-book",
    ),
    "timeline": MonitoredEndpoint(
        id="timeline",
        name="API Timeline",
        url=f"{FACULTY_BASE_URL}/api/v2/timeline.json",
        method=HttpMethod.GET,
        timeout=5,
        description="Timeline general de actividades y noticias.",
        icon="bi-clock-history",
    ),
    "planes_estudio": MonitoredEndpoint(
        id="planes_estudio",
        name="Planes de Estudio",
        url=f"{CONTENT_BASE_URL}/PLANES_ESTUDIOS",
        method=HttpMethod.GET,
        timeout=5,
        description="Planes de estudios de las carreras.",
        icon="bi-journal-bookmark",
    ),
    "calendario": MonitoredEndpoint(
        id="calendario",
        name="Calendario Académico",
        url=f"{CONTENT_BASE_URL}/CALENDARIO_ACADEMICO",
        method=HttpMethod.GET,
        timeout=5,
        description="Calendario con fechas de exámenes e inscripciones.",
        icon="bi-calendar-event",
    ),
    "n8n": MonitoredEndpoint(
        id="n8n",
        name="Orquestador IA (n8n)",
        url=f"{N8N_BASE_URL}/",
        method=HttpMethod.GET,
        timeout=5,
        description="Motor de orquestación de flujos de IA.",
        icon="bi-cpu",
    ),
}


def get_endpoints():
    """Retorna la lista de endpoints registrados."""
    return list(ENDPOINTS.values())


def check_endpoint(endpoint_id):
    """Ejecuta health check para un endpoint específico. Retorna None si no existe."""
    endpoint = ENDPOINTS.get(endpoint_id)
    if endpoint is None:
        return None
    return _execute_check(endpoint)


def check_all():
    """Ejecuta health check para todos los endpoints registrados."""
    return [_execute_check(ep) for ep in ENDPOINTS.values()]


def _execute_check(endpoint):
    """Realiza la petición HTTP y retorna el resultado."""
    try:
        response = requests.request(
            endpoint.method.value,
            endpoint.url,
            timeout=endpoint.timeout,
        )

        is_ok = 200 <= response.status_code < 300
        status = ServiceStatus.OPERATIONAL if is_ok else ServiceStatus.DEGRADED
        latency_ms = response.elapsed.total_seconds() * 1000

        return HealthCheckResult(
            endpoint_id=endpoint.id,
            endpoint_name=endpoint.name,
            status=status,
            status_code=response.status_code,
            latency_ms=latency_ms,
            url=endpoint.url,
            icon=endpoint.icon,
        )

    except requests.exceptions.ConnectionError:
        return HealthCheckResult(
            endpoint_id=endpoint.id,
            endpoint_name=endpoint.name,
            status=ServiceStatus.UNAVAILABLE,
            url=endpoint.url,
            error="No se pudo establecer conexión con el servidor.",
            icon=endpoint.icon,
        )

    except requests.exceptions.Timeout:
        return HealthCheckResult(
            endpoint_id=endpoint.id,
            endpoint_name=endpoint.name,
            status=ServiceStatus.TIMEOUT,
            url=endpoint.url,
            error="El servidor tardó demasiado en responder.",
            icon=endpoint.icon,
        )

    except Exception as e:
        return HealthCheckResult(
            endpoint_id=endpoint.id,
            endpoint_name=endpoint.name,
            status=ServiceStatus.CRITICAL,
            url=endpoint.url,
            error=str(e),
            icon=endpoint.icon,
        )
