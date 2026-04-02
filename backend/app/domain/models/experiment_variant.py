from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class ExperimentVariant(Base):
    __tablename__ = "experiment_variants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    population_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    engagement_lift: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    experiment = relationship("Experiment", back_populates="variants")
