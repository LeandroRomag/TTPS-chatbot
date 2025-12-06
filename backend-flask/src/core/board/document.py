from sqlalchemy import String, DateTime, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.auth.user import User 

class Document(Base):
    __tablename__ = 'documents'

    # Attributes
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(120), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    file_path: Mapped[str] = mapped_column(String(255), nullable=False)

    uploaded_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    uploader: Mapped[User] = relationship("User", back_populates="uploaded_documents")

    # Methods
    def __repr__(self):
        return f'<Document {self.title}>'
    