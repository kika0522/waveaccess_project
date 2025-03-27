from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Report(Base):
    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    results: Mapped[JSON] = mapped_column(JSON, nullable=True)