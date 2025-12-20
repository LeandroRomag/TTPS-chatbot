from datetime import datetime, timezone
from src.core.auth.system_flag import SystemFlag, SystemFlagType
from src.core.database import db


def get_all_flags(include_deleted: bool = False) -> list[SystemFlag]:
    """Obtiene todas las flags del sistema ordenadas por tipo."""
    query = db.session.query(SystemFlag)
    if not include_deleted:
        query = query.filter(SystemFlag.deleted_at.is_(None))
    return query.order_by(SystemFlag.type).all()


def get_flag_by_id(flag_id: int) -> SystemFlag | None:
    """Obtiene una flag por su ID."""
    return db.session.get(SystemFlag, flag_id)


def get_flag_by_type(flag_type: SystemFlagType, include_deleted: bool = False) -> SystemFlag | None:
    """Obtiene una flag activa por su tipo."""
    query = db.session.query(SystemFlag).filter_by(type=flag_type)
    if not include_deleted:
        query = query.filter(SystemFlag.deleted_at.is_(None))
    return query.first()


def is_flag_enabled(flag_type: SystemFlagType) -> bool:
    """
    Verifica si una flag está habilitada.
    Retorna False si la flag no existe o está eliminada (comportamiento seguro).
    """
    flag = get_flag_by_type(flag_type)  # Ya filtra eliminadas
    return flag.enabled if flag else False


def toggle_flag(flag_id: int) -> bool:
    """
    Alterna el estado de una flag.
    Retorna True si se actualizó correctamente, False si no se encontró o está eliminada.
    """
    flag = get_flag_by_id(flag_id)
    if flag and not flag.is_deleted:
        flag.enabled = not flag.enabled
        db.session.commit()
        return True
    return False


def create_flag(flag_type: SystemFlagType, enabled: bool = False) -> SystemFlag:
    """
    Crea una nueva flag del sistema.
    Nota: Verificar que no exista antes de llamar esta función.
    """
    flag = SystemFlag(type=flag_type, enabled=enabled)
    db.session.add(flag)
    db.session.commit()
    return flag


def delete_flag(flag_id: int) -> bool:
    """
    Elimina lógicamente una flag del sistema (soft delete).
    Retorna True si se eliminó correctamente, False si no se encontró o ya estaba eliminada.
    """
    flag = get_flag_by_id(flag_id)
    if flag and not flag.is_deleted:
        flag.deleted_at = datetime.now(timezone.utc)
        db.session.commit()
        return True
    return False


def restore_flag(flag_id: int) -> bool:
    """
    Restaura una flag eliminada lógicamente.
    Retorna True si se restauró correctamente, False si no se encontró o no estaba eliminada.
    """
    flag = get_flag_by_id(flag_id)
    if flag and flag.is_deleted:
        flag.deleted_at = None
        db.session.commit()
        return True
    return False


def get_available_flag_types() -> list[SystemFlagType]:
    """
    Retorna los tipos de flag que aún no han sido creados.
    Útil para mostrar en un formulario de creación.
    """
    existing_types = {flag.type for flag in get_all_flags()}
    return [ft for ft in SystemFlagType if ft not in existing_types]

