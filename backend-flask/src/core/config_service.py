from src.core.database import db
# Ajusta la importación según donde hayas puesto el modelo SystemConfig
from src.core.board.config import SystemConfig 

def get_config(key, default=None):
    """Obtiene un valor de configuración de la BD"""
    try:
        config = db.session.query(SystemConfig).get(key)
        return config.value if config else default
    except Exception:
        return default

def set_config(key, value):
    """Guarda o actualiza un valor de configuración"""
    try:
        config = db.session.query(SystemConfig).get(key)
        if not config:
            config = SystemConfig(key=key)
            db.session.add(config)
        config.value = str(value)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e