"""
Servicio de monitoreo de endpoints externos.
Funciones para verificar la disponibilidad y estado de las APIs.
"""
import httpx
from datetime import datetime, timezone
from typing import Optional
from src.core.database import db
from src.core.monitoring.endpoint_status import EndpointStatus, HealthStatus, EndpointType


# Configuración
TIMEOUT_SECONDS = 10
DEGRADED_THRESHOLD_MS = 3000  # 3 segundos = degradado

# Endpoints a monitorear (URLs de producción)
ENDPOINTS_CONFIG = [
    # API de Gestión Docente
    {
        "name": "Materias - Lista",
        "description": "Obtiene la lista completa de materias disponibles",
        "url": "https://gestiondocente.info.unlp.edu.ar/api/v2/materias.json",
        "endpoint_type": EndpointType.GESTION_DOCENTE
    },
    {
        "name": "Estado Actual Facultad",
        "description": "Estado actual de la facultad y horarios",
        "url": "https://gestiondocente.info.unlp.edu.ar/reservas/api/consulta/estadoactual",
        "endpoint_type": EndpointType.GESTION_DOCENTE
    },
    {
        "name": "Timeline General",
        "description": "Timeline general de actividades",
        "url": "https://gestiondocente.info.unlp.edu.ar/api/v2/timeline.json",
        "endpoint_type": EndpointType.GESTION_DOCENTE
    },
    # API de Contenido Académico
    {
        "name": "Planes de Estudios",
        "description": "Planes de estudios disponibles",
        "url": "https://gestionapp.info.unlp.edu.ar/api/PLANES_ESTUDIOS",
        "endpoint_type": EndpointType.CONTENIDO_ACADEMICO
    },
    {
        "name": "Calendario Académico",
        "description": "Calendario académico con fechas importantes",
        "url": "https://gestionapp.info.unlp.edu.ar/api/CALENDARIO_ACADEMICO",
        "endpoint_type": EndpointType.CONTENIDO_ACADEMICO
    },
]


def init_endpoints() -> None:
    """
    Inicializa los endpoints en la base de datos si no existen.
    Llamar al iniciar la aplicación después de crear las tablas.
    """
    for config in ENDPOINTS_CONFIG:
        existing = db.session.query(EndpointStatus).filter_by(url=config["url"]).first()
        if not existing:
            endpoint = EndpointStatus(
                name=config["name"],
                description=config.get("description"),
                url=config["url"],
                endpoint_type=config["endpoint_type"]
            )
            db.session.add(endpoint)
    
    db.session.commit()


def _determine_status(status_code: int, response_time_ms: int) -> HealthStatus:
    """Determina el estado de salud basado en el código HTTP y tiempo de respuesta."""
    if 200 <= status_code < 300:
        if response_time_ms > DEGRADED_THRESHOLD_MS:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
    elif 300 <= status_code < 400:
        return HealthStatus.DEGRADED
    else:
        return HealthStatus.UNHEALTHY


def check_endpoint(endpoint: EndpointStatus) -> EndpointStatus:
    """
    Verifica un endpoint individual y actualiza su estado en la base de datos.
    
    Args:
        endpoint: El endpoint a verificar
        
    Returns:
        El endpoint actualizado
    """
    now = datetime.now(timezone.utc)
    endpoint.last_checked = now
    
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            start_time = datetime.now()
            response = client.get(endpoint.url)
            end_time = datetime.now()
            
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            endpoint.status_code = response.status_code
            endpoint.response_time_ms = response_time_ms
            endpoint.status = _determine_status(response.status_code, response_time_ms)
            endpoint.error_message = None
            
            if endpoint.status == HealthStatus.HEALTHY:
                endpoint.last_success = now
            else:
                endpoint.last_failure = now
                
    except httpx.TimeoutException:
        endpoint.status = HealthStatus.UNREACHABLE
        endpoint.status_code = None
        endpoint.response_time_ms = None
        endpoint.error_message = "Timeout: El servidor no respondió a tiempo"
        endpoint.last_failure = now
        
    except httpx.ConnectError as e:
        endpoint.status = HealthStatus.UNREACHABLE
        endpoint.status_code = None
        endpoint.response_time_ms = None
        endpoint.error_message = f"Error de conexión: {str(e)}"
        endpoint.last_failure = now
        
    except Exception as e:
        endpoint.status = HealthStatus.UNREACHABLE
        endpoint.status_code = None
        endpoint.response_time_ms = None
        endpoint.error_message = f"Error inesperado: {str(e)}"
        endpoint.last_failure = now
    
    db.session.commit()
    return endpoint


def check_all_endpoints() -> list[EndpointStatus]:
    """
    Verifica todos los endpoints.
    Esta función es llamada por el scheduler cada 24 horas.
    
    Returns:
        Lista de todos los endpoints verificados
    """
    endpoints = db.session.query(EndpointStatus).all()
    
    for endpoint in endpoints:
        check_endpoint(endpoint)
    
    return endpoints


def manual_check(endpoint_id: int) -> Optional[EndpointStatus]:
    """
    Verificación manual de un endpoint específico.
    
    Args:
        endpoint_id: ID del endpoint a verificar
        
    Returns:
        El endpoint actualizado o None si no existe
    """
    endpoint = db.session.query(EndpointStatus).filter_by(id=endpoint_id).first()
    
    if endpoint:
        return check_endpoint(endpoint)
    
    return None


def get_all_status() -> list[EndpointStatus]:
    """
    Obtiene el estado de todos los endpoints.
    
    Returns:
        Lista de todos los endpoints
    """
    return db.session.query(EndpointStatus).order_by(EndpointStatus.endpoint_type).all()


def get_status_summary() -> dict:
    """
    Obtiene un resumen del estado de todos los endpoints.
    
    Returns:
        Diccionario con conteo por estado
    """
    endpoints = get_all_status()
    
    summary = {
        "total": len(endpoints),
        "healthy": 0,
        "degraded": 0,
        "unhealthy": 0,
        "unreachable": 0
    }
    
    for endpoint in endpoints:
        if endpoint.status == HealthStatus.HEALTHY:
            summary["healthy"] += 1
        elif endpoint.status == HealthStatus.DEGRADED:
            summary["degraded"] += 1
        elif endpoint.status == HealthStatus.UNHEALTHY:
            summary["unhealthy"] += 1
        else:
            summary["unreachable"] += 1
    
    return summary
