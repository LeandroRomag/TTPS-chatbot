from typing import TYPE_CHECKING
from enum import Enum as PyEnum
from src.core.database import Base
from sqlalchemy import String, Enum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

if TYPE_CHECKING:
    from src.core.board.document import Document

class UserRole(PyEnum):
    ADMIN = 'admin'    # Administrador (puede subir documentos y gestionar sistema)

"""
Propósito: Representa a usuarios que acceden vía web al sistema.
Se registran manualmente con email y contraseña.
"""
class User(Base):
    __tablename__ = 'users'

    # Attributes
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    apellido: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    system_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name='user_role'), 
        nullable=False, 
        default=UserRole.ADMIN
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None
    )

    # Relationships
    # Documentos subidos por este usuario
    # Si se elimina el usuario, uploaded_by queda en NULL (no se eliminan documentos)
    uploaded_documents: Mapped[list["Document"]] = relationship(
        back_populates="uploader",
        foreign_keys="Document.uploaded_by"
    )

    # Properties
    @property
    def is_active(self) -> bool:
        """Retorna True si el usuario está activo y no eliminado."""
        return self.active and not self.is_deleted

    @property
    def is_sysadmin(self) -> bool:
        """Retorna True si el usuario es administrador del sistema."""
        return self.system_admin
    
    @property
    def is_admin(self) -> bool:
        """Retorna True si el usuario tiene rol de administrador."""
        return self.role == UserRole.ADMIN

    @property
    def is_deleted(self) -> bool:
        """Retorna True si el usuario fue eliminado lógicamente."""
        return self.deleted_at is not None

    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del usuario."""
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        status = "deleted" if self.is_deleted else ("active" if self.active else "inactive")
        return f'<User {self.email} ({status})>'