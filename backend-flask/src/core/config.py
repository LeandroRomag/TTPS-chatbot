import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')


class DevelopmentConfig(Config):
    DEBUG = True
    
    # Build database URL from individual components
    DB_NAME = os.getenv('DB_NAME', 'chatbot_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # flask-sqlalchemy-lite requires SQLALCHEMY_ENGINES dict
    # Usamos URL.create() para manejar caracteres especiales en credenciales
    # client_encoding='utf8' resuelve UnicodeDecodeError en Windows con locale cp1252
    SQLALCHEMY_ENGINES = {
        'default': {
            'url': URL.create(
                drivername="postgresql",
                username=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '5432')),
                database=os.getenv('DB_NAME', 'chatbot_db')
            ),
            'client_encoding': 'utf8'
        }
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