from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiseaseReference(Base):
    __tablename__ = "diseases_reference"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    crop: Mapped[str] = mapped_column(String(50), nullable=False)
    disease_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    disease_display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    prevention_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_healthy_label: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
