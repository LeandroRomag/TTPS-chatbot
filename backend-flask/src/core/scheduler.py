"""
Scheduler para tareas programadas.
Utiliza APScheduler para ejecutar verificaciones periódicas de endpoints.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask
import atexit

# Instancia global del scheduler
scheduler = BackgroundScheduler(daemon=True)


def init_scheduler(app: Flask) -> None:
    """
    Inicializa el scheduler con la aplicación Flask.
    Configura el job de verificación de endpoints cada 24 horas.
    
    Args:
        app: Instancia de la aplicación Flask
    """
    def check_endpoints_job():
        """Job wrapper que ejecuta la verificación dentro del contexto de la app."""
        with app.app_context():
            from src.core.services import endpoint_monitor_service
            print("[Scheduler] Ejecutando verificación programada de endpoints...")
            results = endpoint_monitor_service.check_all_endpoints()
            healthy = sum(1 for r in results if r.status.value == 'healthy')
            print(f"[Scheduler] Verificación completada: {healthy}/{len(results)} endpoints saludables")
    
    # Agregar job de verificación de endpoints cada 24 horas
    scheduler.add_job(
        func=check_endpoints_job,
        trigger=IntervalTrigger(hours=24),
        id='endpoint_health_check',
        name='Verificación diaria de endpoints',
        replace_existing=True
    )
    
    # Iniciar el scheduler si no está corriendo
    if not scheduler.running:
        scheduler.start()
        print("[Scheduler] Iniciado - Verificación de endpoints programada cada 24 horas")
    
    # Asegurar que el scheduler se detenga al cerrar la aplicación
    atexit.register(lambda: scheduler.shutdown(wait=False))


def run_immediate_check(app: Flask) -> None:
    """
    Ejecuta una verificación inmediata de todos los endpoints.
    Útil para testing o verificación inicial.
    
    Args:
        app: Instancia de la aplicación Flask
    """
    with app.app_context():
        from src.core.services import endpoint_monitor_service
        endpoint_monitor_service.check_all_endpoints()


def get_next_run_time() -> str:
    """
    Obtiene la próxima hora de ejecución del job de verificación.
    
    Returns:
        String con la próxima fecha/hora de ejecución
    """
    job = scheduler.get_job('endpoint_health_check')
    if job and job.next_run_time:
        return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
    return "No programado"


def is_scheduler_running() -> bool:
    """
    Verifica si el scheduler está activo.
    
    Returns:
        True si está corriendo, False en caso contrario
    """
    return scheduler.running
