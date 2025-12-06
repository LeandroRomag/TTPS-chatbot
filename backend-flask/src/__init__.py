from flask import Flask
from src.core.config import config_by_name
from src.core.database import db
from src.web.controllers.auth_controller import authentication_blueprint

def create_app(env='development', static_folder=None):
    # template_folder es relativo al directorio donde está __init__.py (src/)
    app = Flask(__name__, template_folder='web/templates')

    # Cargar configuración según el entorno
    app.config.from_object(config_by_name[env])

    db.init_app(app)

    # Registro de blueprints
    app.register_blueprint(authentication_blueprint)

    # Comandos
    @app.cli.command('reset-db')
    def reset_db_command():
        reset_db()

    

    return app

    