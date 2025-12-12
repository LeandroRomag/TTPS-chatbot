import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


def _get_required_env(key: str) -> str:
    """Obtiene una variable de entorno requerida. Lanza error si no existe."""
    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"Variable de entorno '{key}' es requerida pero no está definida. "
            f"Copia .env.example a .env y configura las variables."
        )
    return value


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


class DevelopmentConfig(Config):
    DEBUG = True
    
    # Variables de entorno de PostgreSQL (requeridas)
    DB_NAME = os.getenv('DB_NAME', 'chatbot_db')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # Construir URL usando SQLAlchemy URL.create() para manejar caracteres especiales
    @staticmethod
    def _build_database_url():
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        if not db_user or not db_password:
            raise ValueError(
                "PostgreSQL es requerido. Las variables DB_USER y DB_PASSWORD deben estar definidas. "
                "Copia .env.example a .env y configura las credenciales de PostgreSQL."
            )
        
        return URL.create(
            drivername="postgresql",
            username=db_user,
            password=db_password,
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'chatbot_db')
        )
    
    # flask-sqlalchemy-lite requires SQLALCHEMY_ENGINES dict
    # URL.create() maneja automáticamente el encoding de caracteres especiales
    SQLALCHEMY_ENGINES = None  # Se inicializa dinámicamente
    
    def __init__(self):
        if DevelopmentConfig.SQLALCHEMY_ENGINES is None:
            DevelopmentConfig.SQLALCHEMY_ENGINES = {
                'default': str(DevelopmentConfig._build_database_url())
            }


# Inicializar la URL de la base de datos al importar el módulo
try:
    _dev_db_url = DevelopmentConfig._build_database_url()
    DevelopmentConfig.SQLALCHEMY_ENGINES = {'default': str(_dev_db_url)}
except ValueError as e:
    # En desarrollo, mostrar advertencia pero permitir que el módulo se cargue
    # El error se lanzará cuando se intente usar la configuración
    import warnings
    warnings.warn(str(e))
    DevelopmentConfig.SQLALCHEMY_ENGINES = None


class TestingConfig(Config):
    TESTING = True
    # Testing usa SQLite en memoria para tests rápidos
    SQLALCHEMY_ENGINES = {'default': 'sqlite:///:memory:'}


class ProductionConfig(Config):
    DEBUG = False
    
    @staticmethod
    def _build_database_url():
        """En producción, todas las variables son obligatorias."""
        return URL.create(
            drivername="postgresql",
            username=_get_required_env('DB_USER'),
            password=_get_required_env('DB_PASSWORD'),
            host=_get_required_env('DB_HOST'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=_get_required_env('DB_NAME')
        )
    
    SQLALCHEMY_ENGINES = None  # Se debe configurar en producción


# Diccionario para mapear nombres de configuración a clases
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}