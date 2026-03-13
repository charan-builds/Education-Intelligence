from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    graph_path: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)

    questions = relationship("Question", back_populates="topic")
