from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base


class SystemFlagType(Enum):
    MAINTENANCE_MODE = "maintenance_mode"


class SystemFlag(Base):
    __tablename__ = "system_flags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[SystemFlagType] = mapped_column(
        Enum(SystemFlagType, name='system_flag_type'),
        nullable=False,
        unique=True
    )
    enabled: Mapped[bool] = mapped_column(nullable=False)
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

    @property
    def is_deleted(self) -> bool:
        """Retorna True si la flag fue eliminada lógicamente."""
        return self.deleted_at is not None

    def __repr__(self):
        status = "deleted" if self.is_deleted else ("enabled" if self.enabled else "disabled")
        return f'<SystemFlag {self.type.name}: {status}>'

    