"""
Modelo para almacenar el estado de los endpoints externos.
Registra la disponibilidad, tiempo de respuesta y errores de las APIs monitoreadas.
"""
from enum import Enum as PyEnum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base


class EndpointType(PyEnum):
    """Tipo de API del endpoint."""
    GESTION_DOCENTE = 'gestion_docente'
    CONTENIDO_ACADEMICO = 'contenido_academico'


class HealthStatus(PyEnum):
    """Estado de salud del endpoint."""
    HEALTHY = 'healthy'          # Responde correctamente (2xx)
    DEGRADED = 'degraded'        # Responde lento (>3s) o 3xx
    UNHEALTHY = 'unhealthy'      # Error (4xx/5xx)
    UNREACHABLE = 'unreachable'  # Sin conexión/timeout


class EndpointStatus(Base):
    """Modelo para almacenar el estado de los endpoints externos."""
    __tablename__ = 'endpoint_status'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Información del endpoint
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    endpoint_type: Mapped[EndpointType] = mapped_column(
        Enum(EndpointType, name='endpoint_type'),
        nullable=False
    )
    
    # Estado actual
    status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, name='health_status'),
        default=HealthStatus.UNREACHABLE
    )
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timestamps de verificación
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Información de error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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

    def __repr__(self):
        return f'<EndpointStatus {self.name}: {self.status.value}>'
    
    @property
    def status_emoji(self) -> str:
        """Retorna un emoji representativo del estado."""
        emojis = {
            HealthStatus.HEALTHY: '✅',
            HealthStatus.DEGRADED: '⚠️',
            HealthStatus.UNHEALTHY: '❌',
            HealthStatus.UNREACHABLE: '🔌'
        }
        return emojis.get(self.status, '❓')
    
    @property
    def status_badge_class(self) -> str:
        """Retorna la clase Bootstrap para el badge de estado."""
        classes = {
            HealthStatus.HEALTHY: 'bg-success',
            HealthStatus.DEGRADED: 'bg-warning',
            HealthStatus.UNHEALTHY: 'bg-danger',
            HealthStatus.UNREACHABLE: 'bg-secondary'
        }
        return classes.get(self.status, 'bg-secondary')
