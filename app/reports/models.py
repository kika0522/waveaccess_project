from sqlalchemy import Column, JSON, String, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.database import Base
import uuid


class Report(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    results: Mapped[JSON] = mapped_column(JSON, nullable=True)