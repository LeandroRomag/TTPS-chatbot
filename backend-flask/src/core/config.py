import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')



class DevelopmentConfig(Config):
    DEBUG = True
    # Build database URL from individual components (only use Postgres
    # when the user explicitly configured it via environment variables).
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_SCHEMA = os.getenv('DB_SCHEMA')

    # If the environment doesn't explicitly request Postgres (no DB_SCHEMA)
    # or if required connection pieces are missing, fall back to SQLite.
    if not DB_SCHEMA or not (DB_USER and DB_PASSWORD and DB_HOST and DB_NAME):
        sqlite_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'dev.sqlite')
        sqlite_path = os.path.normpath(sqlite_path)
        SQLALCHEMY_ENGINES = {'default': f"sqlite:///{sqlite_path}"}
    else:
        # Use SQLAlchemy URL.create to ensure proper encoding of username/password
        driver = DB_SCHEMA
        if DB_SCHEMA == 'postgresql':
            driver = 'postgresql+psycopg2'

        SQLALCHEMY_ENGINES = {
            'default': str(
                URL.create(
                    drivername=driver,
                    username=DB_USER or None,
                    password=DB_PASSWORD or None,
                    host=DB_HOST or None,
                    port=int(DB_PORT) if DB_PORT else None,
                    database=DB_NAME or None,
                )
            )
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