from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"


class ServiceStatus(Enum):
    OPERATIONAL = "Operativo"
    DEGRADED = "Degradado"
    UNAVAILABLE = "No Disponible"
    TIMEOUT = "Tiempo de espera agotado"
    CRITICAL = "Fallo Crítico"


@dataclass(frozen=True)
class MonitoredEndpoint:
    id: str
    name: str
    url: str
    method: HttpMethod = HttpMethod.GET
    timeout: int = 5
    description: str = ""
    icon: str = "bi-server"


@dataclass
class HealthCheckResult:
    endpoint_id: str
    endpoint_name: str
    status: ServiceStatus
    status_code: int | None = None
    latency_ms: float | None = None
    url: str = ""
    error: str | None = None
    checked_at: datetime = field(default_factory=datetime.now)
    icon: str = "bi-server"

    @property
    def is_healthy(self) -> bool:
        return self.status == ServiceStatus.OPERATIONAL

    @property
    def latency_display(self) -> str:
        if self.latency_ms is not None:
            return f"{self.latency_ms:.0f} ms"
        return "-"

    @property
    def status_code_display(self) -> str:
        if self.status_code is not None:
            return str(self.status_code)
        return "N/A"

    @property
    def checked_at_display(self) -> str:
        return self.checked_at.strftime("%d/%m/%Y %H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "endpoint_id": self.endpoint_id,
            "endpoint_name": self.endpoint_name,
            "status": self.status.value,
            "status_code": self.status_code,
            "latency_ms": self.latency_ms,
            "latency_display": self.latency_display,
            "status_code_display": self.status_code_display,
            "url": self.url,
            "is_healthy": self.is_healthy,
            "error": self.error,
            "checked_at": self.checked_at_display,
            "icon": self.icon,
        }
