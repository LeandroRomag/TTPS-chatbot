from src.core.database import Base
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

class SystemConfig(Base):
    __tablename__ = 'system_config'

    # Clave primaria será el nombre de la configuración (ej: "maintenance_mode", "maintenance_message")
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f'<Config {self.key}: {self.value}>'