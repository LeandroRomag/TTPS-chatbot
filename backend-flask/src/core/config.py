import os
from dotenv import load_dotenv

load_dotenv()

# Calcular ruta base del proyecto (2 niveles arriba de este archivo: src/core/config.py -> raíz)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')


class DevelopmentConfig(Config):
    DEBUG = True
    
    # SQLite database configuration
    # Ruta absoluta al archivo de base de datos
    DB_PATH = os.path.join(BASE_DIR, os.getenv('DB_PATH', 'data/chatbot.db'))
    
    # flask-sqlalchemy-lite requires SQLALCHEMY_ENGINES dict
    # Usamos ruta absoluta para evitar problemas con el directorio de trabajo
    SQLALCHEMY_ENGINES = {
        'default': f'sqlite:///{DB_PATH}'
    }


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


# Diccionario para mapear nombres de configuración a clases
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}