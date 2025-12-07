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
    role: Mapped[str] = mapped_column(
        Enum(UserRole, name='user_role'), 
        nullable=False, 
        default='admin'
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    # Documentos subidos por este usuario
    # Si se elimina el usuario, uploaded_by queda en NULL (no se eliminan documentos)
    uploaded_documents: Mapped[list["Document"]] = relationship(
        back_populates="uploader",
        foreign_keys="Document.uploaded_by"
    )

    # Methods
    def is_active(self):
        """Usa el campo active de la BD."""
        return self.active

    def is_sysadmin(self):
        """Usa el campo sysadmin de la BD."""
        return self.sysadmin
    
    def is_admin(self):
        """Usa el campo role de la BD."""
        return self.role == UserRole.ADMIN.value

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'