from datetime import datetime, timezone
from src.core.auth.user import User, UserRole
from src.core.database import db


# ============================================================
# Consultas
# ============================================================

def get_all_users(include_deleted: bool = False) -> list[User]:
    """Obtiene todos los usuarios ordenados por email."""
    query = db.session.query(User)
    if not include_deleted:
        query = query.filter(User.deleted_at.is_(None))
    return query.order_by(User.email).all()


def get_user_by_id(user_id: int) -> User | None:
    """Obtiene un usuario por su ID (incluye eliminados)."""
    return db.session.get(User, user_id)


def get_user_by_email(email: str, include_deleted: bool = False) -> User | None:
    """Obtiene un usuario por su email."""
    query = db.session.query(User).filter_by(email=email)
    if not include_deleted:
        query = query.filter(User.deleted_at.is_(None))
    return query.first()


def get_active_users() -> list[User]:
    """Obtiene solo usuarios activos (no eliminados y con active=True)."""
    return db.session.query(User).filter(
        User.deleted_at.is_(None),
        User.active == True
    ).order_by(User.email).all()


# ============================================================
# Creación y actualización
# ============================================================

def create_user(
    nombre: str,
    apellido: str,
    email: str,
    password_hash: str,
    role: UserRole = UserRole.ADMIN,
    system_admin: bool = False,
    active: bool = True
) -> User:
    """
    Crea un nuevo usuario.
    Nota: El password_hash debe venir ya hasheado desde el controlador/auth.
    """
    user = User(
        nombre=nombre,
        apellido=apellido,
        email=email,
        password_hash=password_hash,
        role=role,
        system_admin=system_admin,
        active=active
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user(
    user_id: int,
    nombre: str | None = None,
    apellido: str | None = None,
    email: str | None = None,
    role: UserRole | None = None,
    active: bool | None = None
) -> User | None:
    """
    Actualiza los datos de un usuario.
    Solo actualiza los campos que no sean None.
    """
    user = get_user_by_id(user_id)
    if not user or user.is_deleted:
        return None
    
    if nombre is not None:
        user.nombre = nombre
    if apellido is not None:
        user.apellido = apellido
    if email is not None:
        user.email = email
    if role is not None:
        user.role = role
    if active is not None:
        user.active = active
    
    db.session.commit()
    return user


def update_password(user_id: int, new_password_hash: str) -> bool:
    """Actualiza la contraseña de un usuario."""
    user = get_user_by_id(user_id)
    if not user or user.is_deleted:
        return False
    
    user.password_hash = new_password_hash
    db.session.commit()
    return True


# ============================================================
# Activación / Desactivación
# ============================================================

def toggle_active(user_id: int) -> bool:
    """Alterna el estado activo de un usuario."""
    user = get_user_by_id(user_id)
    if not user or user.is_deleted:
        return False
    
    user.active = not user.active
    db.session.commit()
    return True


# ============================================================
# Eliminación lógica (Soft Delete)
# ============================================================

def delete_user(user_id: int) -> bool:
    """
    Elimina lógicamente un usuario (soft delete).
    Marca deleted_at con la fecha actual.
    """
    user = get_user_by_id(user_id)
    if not user or user.is_deleted:
        return False
    
    user.deleted_at = datetime.now(timezone.utc)
    user.active = False  # También lo desactivamos
    db.session.commit()
    return True


def restore_user(user_id: int) -> bool:
    """
    Restaura un usuario eliminado lógicamente.
    Limpia deleted_at pero NO reactiva automáticamente.
    """
    user = get_user_by_id(user_id)
    if not user or not user.is_deleted:
        return False
    
    user.deleted_at = None
    db.session.commit()
    return True


# ============================================================
# Validaciones
# ============================================================

def email_exists(email: str, exclude_user_id: int | None = None) -> bool:
    """
    Verifica si un email ya está en uso.
    Opcionalmente excluye un usuario (útil para updates).
    """
    query = db.session.query(User).filter_by(email=email)
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    return query.first() is not None
