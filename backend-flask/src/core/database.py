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
    try:
        # SQLAlchemy URL may hide password; show full repr for debugging
        url = engine.url
        try:
            url_str = url.render_as_string(hide_password=False)
        except Exception:
            url_str = str(url)
        print(f"Engine URL (repr): {repr(url_str)}")
    except Exception as e:
        print(f"Could not obtain engine URL: {e}")

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    from src.core.auth.user import User as Usuario, UserRole
    superAdmin = Usuario(
        nombre="Super",
        apellido="Admin",
        email="admin@gmail.com",
        password_hash=generate_password_hash("admin123"),
        role=UserRole.ADMIN,
        active=True,
        system_admin=True,
    )

    db.session.add(superAdmin)
    db.session.commit()

    print("Database reset. Superadmin created!")
