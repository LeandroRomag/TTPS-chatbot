from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from werkzeug.security import generate_password_hash
db = SQLAlchemy()
class Base(DeclarativeBase):
    pass

# Configurar la base de datos en la app flask
def init_app(app):
    db.init_app(app)
    return app

def reset_db():
    
    print("Resetting database...")
    engine = db.get_engine()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = db.sessionmaker(bind=engine)
    session = Session()
    from src.core.auth.user import User as Usuario
    superAdmin = Usuario(
        nombre="Super",
        apellido="Admin",
        email="admin@gmail.com",
        password_hash=generate_password_hash("admin123"),
        rol="admin",
        activo=True,
        system_admin=True,
    )

    session.add(superAdmin)
    session.commit()
    session.close()

    print("Database reset. Superadmin created!")
