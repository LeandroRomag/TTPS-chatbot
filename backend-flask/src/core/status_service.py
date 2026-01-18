import requests
import os

# --- CONFIGURACIÓN DE URLS ---
# Basado en tu documentación:
# Producción: https://gestiondocente.info.unlp.edu.ar
# Desarrollo: http://163.10.22.42
FACULTY_BASE_URL = os.getenv("FACULTY_API_URL", "https://gestiondocente.info.unlp.edu.ar")

# Endpoint específico para chequear estado (extraído de endpoints-info.md sección 1.2)
FACULTY_HEALTH_ENDPOINT = "/reservas/api/consulta/estadoactual"

# URL de n8n (Orquestador IA)
N8N_BASE_URL = os.getenv("N8N_HOST", "http://localhost:5678")

def check_service_health(name, url, method="GET", timeout=3):
    """
    Realiza una petición HTTP para verificar el estado de un servicio.
    """
    try:
        response = requests.request(method, url, timeout=timeout)
        
        # Consideramos 'Operativo' si el código es 200-299
        is_active = 200 <= response.status_code < 300
        
        status_label = "Operativo" if is_active else f"Error ({response.status_code})"
        
        return {
            "name": name,
            "status": status_label,
            "code": response.status_code,
            "latency": f"{response.elapsed.total_seconds() * 1000:.0f} ms",
            "is_active": is_active,
            "url": url,
            "error": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "name": name,
            "status": "No Disponible",
            "code": "N/A",
            "latency": "-",
            "is_active": False,
            "url": url,
            "error": "No se pudo establecer conexión con el servidor."
        }
    except requests.exceptions.Timeout:
        return {
            "name": name,
            "status": "Tiempo de espera agotado",
            "code": "Timeout",
            "latency": f"> {timeout*1000} ms",
            "is_active": False,
            "url": url,
            "error": "El servidor tardó demasiado en responder."
        }
    except Exception as e:
        return {
            "name": name,
            "status": "Fallo Crítico",
            "code": "Err",
            "latency": "-",
            "is_active": False,
            "url": url,
            "error": str(e)
        }

def get_system_status():
    """
    Ejecuta las verificaciones requeridas por RF 09.
    """
    results = []

    # 1. RF 09.1 - API Facultad (Gestión Docente)
    # Usamos el endpoint de estado actual que es el más liviano y semánticamente correcto.
    faculty_check_url = f"{FACULTY_BASE_URL}{FACULTY_HEALTH_ENDPOINT}"
    results.append(check_service_health("API Gestión Docente (UNLP)", faculty_check_url))

    # 2. RF 09.2 - Modelo de Lenguaje (n8n)
    # Verificamos la raíz de n8n para confirmar que el orquestador está levantado.
    # Si n8n tiene usuario/pass, esto podría devolver 401 (Unauthorized), 
    # lo cual técnicamente significa que el servicio ESTÁ activo (luz verde), 
    # pero aquí validamos 200-299. Si te da error 401/403 avísame para ajustar la lógica.
    n8n_check_url = f"{N8N_BASE_URL}/" 
    results.append(check_service_health("Orquestador IA (n8n)", n8n_check_url))

    return results