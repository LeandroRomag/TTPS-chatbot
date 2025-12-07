from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

db = SQLAlchemy()

class Base(DeclarativeBase):
    pass

# Configurar la base de datos en la app flask
def init_app(app):
    db.init_app(app)
    return app

def reset_db():
    print("Resetting database...")
    Base.metadata.drop_all(db.get_engine())
    Base.metadata.create_all(db.get_engine())
    print("Database reset.")


