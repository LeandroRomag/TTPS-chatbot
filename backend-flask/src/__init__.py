from flask import Flask
from src.core.config import config_by_name
from src.core.database import db, reset_db 
from src.web.controllers.auth_controller import authentication_blueprint
from src.web.controllers.user_controller import user_blueprint
from src.web.controllers.document_controller import document_blueprint
from src.web.controllers.endpoint_status_controller import endpoint_status_blueprint

# Import models to ensure they are registered with SQLAlchemy
from src.core.auth.user import User
from src.core.board.document import Document
from src.core.monitoring.endpoint_status import EndpointStatus

def create_app(env='development', static_folder=None):
    # template_folder es relativo al directorio donde está __init__.py (src/)
    app = Flask(__name__, template_folder='web/templates')

    # Cargar configuración según el entorno
    app.config.from_object(config_by_name[env])

    db.init_app(app)

    # Registro de blueprints
    app.register_blueprint(authentication_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(document_blueprint)
    app.register_blueprint(endpoint_status_blueprint)

    # Comandos CLI
    @app.cli.command('reset-db')
    def reset_db_command():
        reset_db()

    @app.cli.command('init-endpoints')
    def init_endpoints_command():
        """Inicializa los endpoints a monitorear en la base de datos."""
        from src.core.services import endpoint_monitor_service
        endpoint_monitor_service.init_endpoints()
        print("Endpoints inicializados correctamente.")

    @app.cli.command('check-endpoints')
    def check_endpoints_command():
        """Verifica el estado de todos los endpoints monitoreados."""
        from src.core.services import endpoint_monitor_service
        results = endpoint_monitor_service.check_all_endpoints()
        for r in results:
            print(f"{r.status_emoji} {r.name}: {r.status.value} ({r.response_time_ms}ms)")

    # Inicializar scheduler para verificación automática cada 24 horas
    from src.core.scheduler import init_scheduler
    init_scheduler(app)

    return app