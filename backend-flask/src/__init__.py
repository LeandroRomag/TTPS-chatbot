from flask import Flask, redirect, url_for
from src.core.config import config_by_name
from src.core.database import db, reset_db 
from src.web.controllers.auth_controller import authentication_blueprint
from src.web.controllers.user_controller import user_blueprint
from src.web.controllers.document_controller import document_blueprint
from src.web.controllers.whatsapp_controller import whatsapp_blueprint
from src.web.controllers.system_controller import system_blueprint
from src.web.controllers.status_controller import status_blueprint

# Import models to ensure they are registered with SQLAlchemy
from src.core.auth.user import User
from src.core.board.document import Document
import os
def create_app(env='development', static_folder=None):
    # template_folder es relativo al directorio donde está __init__.py (src/)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))      # .../project/src
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))  # .../project
    
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "web", "templates"),
        static_folder=os.path.join(PROJECT_ROOT, "static")
    )
    # Cargar configuración según el entorno
    app.config.from_object(config_by_name[env])
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    db.init_app(app)

    # Registro de blueprints
    app.register_blueprint(authentication_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(document_blueprint)
    app.register_blueprint(whatsapp_blueprint)
    app.register_blueprint(system_blueprint)
    app.register_blueprint(status_blueprint)
    
    @app.route('/')
    def root():
        return redirect(url_for('authentication.login'))

    # Comandos
    @app.cli.command('reset-db')
    def reset_db_command():
        reset_db()

    

    return app

    