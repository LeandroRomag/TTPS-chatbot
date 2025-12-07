from flask import Flask
from src.core.config import config_by_name
from src.core.database import db, reset_db 
from src.web.controllers.auth_controller import authentication_blueprint
from src.web.controllers.user_controller import user_blueprint
from src.web.controllers.document_controller import document_blueprint

# Import models to ensure they are registered with SQLAlchemy
from src.core.auth.user import User
from src.core.board.document import Document

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

    # Comandos
    @app.cli.command('reset-db')
    def reset_db_command():
        reset_db()

    

    return app

    