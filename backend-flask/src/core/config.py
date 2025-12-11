import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

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
    DB_SCHEMA = os.getenv('DB_SCHEMA', 'postgresql')
    
    # flask-sqlalchemy-lite requires SQLALCHEMY_ENGINES dict
    # quote_plus encodes special characters in password (ó, ñ, @, etc.)
    SQLALCHEMY_ENGINES = {
        'default': f"{os.getenv('DB_SCHEMA', 'postgresql')}://{quote_plus(os.getenv('DB_USER', 'postgres'))}:{quote_plus(os.getenv('DB_PASSWORD', 'postgres'))}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'chatbot_db')}"
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