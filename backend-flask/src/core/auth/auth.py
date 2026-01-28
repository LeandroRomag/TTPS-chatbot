"""
Módulo de Autenticación y Seguridad
Proporciona utilidades para el manejo de autenticación de usuarios,
validaciones de credenciales y operaciones relacionadas con sesiones.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from src.core.auth.user import User
from src.core.services import user_services
from typing import Optional


# ============================================================
# Validaciones de Email
# ============================================================

def is_valid_email(email: str) -> bool:
    """
    Valida el formato básico de un email.
    
    Args:
        email: Email a validar
    
    Returns:
        True si el email tiene formato válido, False en caso contrario
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    # Validación básica: debe contener @
    if "@" not in email:
        return False
    
    local_part, domain = email.rsplit("@", 1)
    
    if not local_part or not domain or "." not in domain:
        return False
    
    return len(email) <= 120


def is_valid_password(password: str) -> tuple[bool, str]:
    """
    Valida la fortaleza de una contraseña.
    
    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    
    Args:
        password: Contraseña a validar
    
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if not password or not isinstance(password, str):
        return False, "La contraseña es requerida."
    
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    
    if not any(c.isupper() for c in password):
        return False, "La contraseña debe contener al menos una mayúscula."
    
    if not any(c.islower() for c in password):
        return False, "La contraseña debe contener al menos una minúscula."
    
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un número."
    
    return True, ""


# ============================================================
# Autenticación de Usuario
# ============================================================

def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Autentica a un usuario con email y contraseña.
    
    Args:
        email: Email del usuario
        password: Contraseña en texto plano
    
    Returns:
        Usuario si la autenticación es exitosa, None en caso contrario
    """
    if not email or not password:
        return None
    
    user = user_services.get_user_by_email(email.strip(), include_deleted=False)
    
    if not user or not user.is_active:
        return None
    
    if not user.check_password(password):
        return None
    
    return user


def validate_credentials(email: str, password: str) -> tuple[bool, str]:
    """
    Valida las credenciales de un usuario.
    Retorna un mensaje descriptivo del resultado.
    
    Args:
        email: Email del usuario
        password: Contraseña en texto plano
    
    Returns:
        Tupla (credenciales_válidas, mensaje)
    """
    if not email or not password:
        return False, "Email y contraseña son requeridos."
    
    if not is_valid_email(email):
        return False, "Email no válido."
    
    user = user_services.get_user_by_email(email.strip(), include_deleted=False)
    
    if not user:
        return False, "Email o contraseña incorrectos."
    
    if not user.is_active:
        return False, "Usuario inactivo. Contacta al administrador."
    
    if not user.check_password(password):
        return False, "Email o contraseña incorrectos."
    
    return True, "Autenticación exitosa."


# ============================================================
# Gestión de Contraseñas
# ============================================================

def generate_password_for_user(password: str) -> Optional[str]:
    """
    Genera un hash de contraseña seguro para almacenar en la base de datos.
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        Hash de la contraseña o None si es inválida
    """
    is_valid, _ = is_valid_password(password)
    if not is_valid:
        return None
    
    return generate_password_hash(password, method='pbkdf2:sha256')


def reset_user_password(user_id: int, new_password: str) -> tuple[bool, str]:
    """
    Cambia la contraseña de un usuario.
    
    Args:
        user_id: ID del usuario
        new_password: Nueva contraseña en texto plano
    
    Returns:
        Tupla (éxito, mensaje)
    """
    # Validar contraseña
    is_valid, error_msg = is_valid_password(new_password)
    if not is_valid:
        return False, error_msg
    
    # Actualizar en base de datos
    success = user_services.update_password(user_id, generate_password_for_user(new_password))
    
    if success:
        return True, "Contraseña actualizada exitosamente."
    else:
        return False, "No se pudo actualizar la contraseña."


# ============================================================
# Información de Usuario
# ============================================================

def get_user_session_data(user: User) -> dict:
    """
    Prepara los datos del usuario para almacenar en sesión.
    
    Args:
        user: Objeto Usuario
    
    Returns:
        Diccionario con datos de sesión del usuario
    """
    return {
        "user_id": user.id,
        "user_email": user.email,
        "user_name": user.full_name,
        "user_role": user.role.value,
        "is_admin": user.is_admin,
        "is_sysadmin": user.is_sysadmin,
    }


def user_has_permission(user: User, required_role: str = "admin") -> bool:
    """
    Verifica si un usuario tiene los permisos necesarios.
    
    Args:
        user: Objeto Usuario
        required_role: Rol requerido (admin, sysadmin)
    
    Returns:
        True si el usuario tiene permisos, False en caso contrario
    """
    if required_role == "sysadmin":
        return user.is_sysadmin
    elif required_role == "admin":
        return user.is_admin
    
    return False
